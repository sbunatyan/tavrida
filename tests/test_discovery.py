import StringIO

import mock

import unittest

from tavrida import discovery
from tavrida import exceptions


class LocalDiscoveryTestCase(unittest.TestCase):

    def test_register_remote_service(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_remote_service(service_name, exchange_name)
        self.assertDictEqual(disc._remote_registry,
                             {"some_service": "some_exchange"})

    def test_register_remote_publisher(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_remote_publisher(service_name, exchange_name)
        self.assertDictEqual(disc._remote_publisher_registry,
                             {"some_service": "some_exchange"})

    def test_register_local_publisher(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_local_publisher(service_name, exchange_name)
        self.assertDictEqual(disc._local_publisher_registry,
                             {"some_service": "some_exchange"})

    def test_unregister_remote_service(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_remote_service(service_name, exchange_name)
        disc.unregister_remote_service(service_name)
        self.assertDictEqual(disc._remote_registry, {})

    def test_unregister_remote_publisher(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_remote_publisher(service_name, exchange_name)
        disc.unregister_remote_publisher(service_name)
        self.assertDictEqual(disc._remote_publisher_registry, {})

    def test_unregister_local_publisher(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_local_publisher(service_name, exchange_name)
        disc.unregister_local_publisher(service_name)
        self.assertDictEqual(disc._local_publisher_registry, {})

    def test_get_remote_positive(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_remote_service(service_name, exchange_name)
        res = disc.get_remote(service_name)
        self.assertEqual(res, exchange_name)

    def test_get_remote_negative(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        self.assertRaises(exceptions.UnableToDiscover,
                          disc.get_remote, service_name)

    def test_get_remote_publisher_positive(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_remote_publisher(service_name, exchange_name)
        res = disc.get_remote_publisher(service_name)
        self.assertEqual(res, exchange_name)

    def test_get_remote_publisher_negative(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        self.assertRaises(exceptions.UnableToDiscover,
                          disc.get_remote_publisher, service_name)

    def test_get_local_publisher_positive(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_local_publisher(service_name, exchange_name)
        res = disc.get_local_publisher(service_name)
        self.assertEqual(res, exchange_name)

    def test_get_local_publisher_negative(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        self.assertRaises(exceptions.UnableToDiscover,
                          disc.get_local_publisher, service_name)

    def test_get_all_exchanges(self):
        disc = discovery.LocalDiscovery()
        service_name = "some_service"
        exchange_name = "some_exchange"
        disc.register_remote_service(service_name, exchange_name)
        disc.register_remote_publisher(service_name, exchange_name)
        disc.register_local_publisher(service_name, exchange_name)
        res = disc.get_all_exchanges()
        self.assertListEqual(res["remote"], [exchange_name])
        self.assertListEqual(res["remote_publisher"], [exchange_name])
        self.assertListEqual(res["local_publisher"], [exchange_name])


VALID_DS_FILE = """
[service1]
exchange=service1_exchange
notifications=service1_notifications

[service2]
exchange=service2_exchange
notifications=service2_notifications

[service3]
exchange=service3_exchange
notifications=service3_notifications

[service4]
exchange=service4_exchange
"""


class FileBasedDiscoveryServiceTestCase(unittest.TestCase):

    @mock.patch('__builtin__.open')
    def setUp(self, open_mock):
        dsfile_ini = StringIO.StringIO(VALID_DS_FILE)
        open_mock.return_value = dsfile_ini

        self.ds = discovery.FileBasedDiscoveryService(
            'ds.ini',
            'service1',
            subscriptions=['service2', 'service3'])

    def test_get_remote_service1(self):
        self.assertRaises(exceptions.UnableToDiscover,
                          self.ds.get_remote,
                          'service1')

    def test_get_remote_service2(self):
        self.assertEqual(self.ds.get_remote('service2'),
                         'service2_exchange')

    def test_get_remote_service3(self):
        self.assertEqual(self.ds.get_remote('service3'),
                         'service3_exchange')

    def test_get_remote_service4(self):
        self.assertEqual(self.ds.get_remote('service4'),
                         'service4_exchange')

    def test_get_local_publisher(self):
        self.assertEqual(self.ds.get_local_publisher('service1'),
                         'service1_notifications')

    def test_service_without_local_publisher(self):
        with mock.patch('__builtin__.open') as open_mock:
            dsfile_ini = StringIO.StringIO(VALID_DS_FILE)
            open_mock.return_value = dsfile_ini

            ds = discovery.FileBasedDiscoveryService(
                'ds.ini',
                'service4')

        self.assertRaises(exceptions.UnableToDiscover,
                          ds.get_local_publisher,
                          'service4')

    def test_get_remote_publisher_service2(self):
        self.assertEqual(self.ds.get_remote_publisher('service2'),
                         'service2_notifications')

    def test_get_remote_publisher_service3(self):
        self.assertEqual(self.ds.get_remote_publisher('service3'),
                         'service3_notifications')

    def test_get_remote_publisher_service4(self):
        self.assertRaises(exceptions.UnableToDiscover,
                          self.ds.get_remote_publisher,
                          'service4')

    def test_get_all_exchanges(self):
        a = self.ds.get_all_exchanges()

        self.assertEqual(set(a['local_publisher']),
                         {'service1_notifications'})

        self.assertEqual(set(a['remote_publisher']),
                         {'service2_notifications',
                          'service3_notifications'})

        self.assertEqual(set(a['remote']),
                         {'service2_exchange',
                          'service3_exchange',
                          'service4_exchange'})


class FileBasedDiscoveryServiceNegativeTestCase(unittest.TestCase):

    @mock.patch('__builtin__.open')
    def test_bad_subscription_name(self, open_mock):
        dsfile_ini = StringIO.StringIO(VALID_DS_FILE)
        open_mock.return_value = dsfile_ini

        self.assertRaises(exceptions.ServiceIsNotRegister,
                          discovery.FileBasedDiscoveryService,
                          'ds.ini',
                          'service1',
                          ['service2', 'serviceX'])

    @mock.patch('__builtin__.open')
    def test_bad_service_name(self, open_mock):
        dsfile_ini = StringIO.StringIO(VALID_DS_FILE)
        open_mock.return_value = dsfile_ini

        self.assertRaises(exceptions.ServiceIsNotRegister,
                          discovery.FileBasedDiscoveryService,
                          'ds.ini',
                          'serviceX')

    @mock.patch('__builtin__.open')
    def test_bad_subscription(self, open_mock):
        """Subscribe to service without notifications exchange."""
        dsfile_ini = StringIO.StringIO(VALID_DS_FILE)
        open_mock.return_value = dsfile_ini

        self.assertRaises(exceptions.CantRegisterRemotePublisher,
                          discovery.FileBasedDiscoveryService,
                          'ds.ini',
                          'service1',
                          subscriptions=['service4'])
