import unittest

import mock

from tavrida import middleware


class MiddlewareTestCase(unittest.TestCase):

    def setUp(self):
        super(MiddlewareTestCase, self).setUp()
        self.middleware = middleware.Middleware()

    def test_middleware_process(self):
        message = mock.MagicMock()
        res = self.middleware.process(message)
        self.assertEqual(res, message)
