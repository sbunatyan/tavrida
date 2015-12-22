import unittest

import pika

from tavrida import config


class ConnectionConfigTestCase(unittest.TestCase):

    def setUp(self):
        super(ConnectionConfigTestCase, self).setUp()
        self.user = "user"
        self.password = "password"
        self.credentials = config.Credentials(self.user, self.password)
        self.host = "host"
        self.config = config.ConnectionConfig(self.host, self.credentials)

    def test_to_pika_params_no_client_reconenct(self):
        res = self.config.to_pika_params()
        self.assertEqual((lambda: isinstance(res,
                                             pika.ConnectionParameters))(),
                         True)
