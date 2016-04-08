import StringIO

import mock
import unittest

from tavrida import dsfile


VALID_DSFILE = """
[service1]
exchange=service1_exchange
notifications=service1_notifications

[service2]
exchange=service2_exchange
"""


class PositiveDSFileTestCase(unittest.TestCase):
    """This TestCase uses VALID_DSFILE
    """

    @mock.patch('__builtin__.open')
    def setUp(self, open_mock):
        dsfile_ini = StringIO.StringIO(VALID_DSFILE)
        open_mock.return_value = dsfile_ini

        self.dsf = dsfile.DSFile("dsfile.ini")

    def test_services_property(self):
        """Check that services property returns service1 and service2"""
        self.assertEqual(set(self.dsf.services),
                         {'service1', 'service2'})

    def test_dsf_iterable(self):
        """Check that DSFile iterator returns service1 and service2"""
        self.assertEqual(set([x for x in self.dsf]),
                         {'service1', 'service2'})

    def test_in_operator_true(self):
        """Check that 'in' operator works if item exists"""
        self.assertTrue('service1' in self.dsf)

    def test_in_operator_false(self):
        """Check that 'in' operator works if item doesn't exist"""
        self.assertFalse('serviceX' in self.dsf)

    def test_get_service_by_name(self):
        """Check that I can get service record by name"""
        entry = self.dsf['service1']
        self.assertEqual(entry.service_name, 'service1')

    def test_service1_record(self):
        """Check that service1 record is valid"""
        entry = self.dsf['service1']
        self.assertEqual(entry.service_name, 'service1')
        self.assertEqual(entry.service_exchange, 'service1_exchange')
        self.assertEqual(entry.notifications_exchange,
                         'service1_notifications')

    def test_service2_record(self):
        """Check that service2 record is valid"""
        entry = self.dsf['service2']
        self.assertEqual(entry.service_name, 'service2')
        self.assertEqual(entry.service_exchange, 'service2_exchange')
        self.assertEqual(entry.notifications_exchange, None)
