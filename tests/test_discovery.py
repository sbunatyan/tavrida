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
