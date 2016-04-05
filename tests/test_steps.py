import logging
import mock
import unittest

from tavrida import messages
from tavrida import steps


class ValidateTestCase(unittest.TestCase):

    def setUp(self):
        super(ValidateTestCase, self).setUp()
        self.step = steps.ValidateMessageMiddleware()

    def test_process(self):
        amqp_message = mock.MagicMock()
        res = self.step.process(amqp_message)
        amqp_message.validate.assert_called_once_with()
        self.assertEqual(res, amqp_message)


class CreateMessageTestCase(unittest.TestCase):

    def setUp(self):
        super(CreateMessageTestCase, self).setUp()
        self.step = steps.CreateMessageMiddleware()

    @mock.patch.object(messages, "IncomingMessageFactory")
    def test_process(self, factory_mock):
        message_body = mock.MagicMock()
        res = self.step.process(message_body)
        factory_mock().create.assert_called_once_with(message_body)
        self.assertEqual(res, factory_mock().create())


class CreateAMQPTestCase(unittest.TestCase):

    def setUp(self):
        super(CreateAMQPTestCase, self).setUp()
        self.step = steps.CreateAMQPMiddleware()

    @mock.patch.object(messages.AMQPMessage, "create_from_message")
    def test_process(self, create_mock):
        message = mock.MagicMock()
        res = self.step.process(message)
        create_mock.assert_called_once_with(message)
        self.assertEqual(res, create_mock())


class LoggingMiddlewareTestCase(unittest.TestCase):

    def setUp(self):
        super(LoggingMiddlewareTestCase, self).setUp()

        class TestedController(steps.LoggingMiddleware):
            def process(self, message):
                pass

        self._middleware = TestedController()

    def test_hide_sensitive_data(self):
        """[Positive] _hide_sensitive_data hides secret values."""
        input_headers = {'proxy-authorization': 'secret proxy-authorization',
                         'authorization': 'secret authorization',
                         'phone': 'non-secret phone'}
        self.assertDictEqual(
            self._middleware._hide_sensitive_data(input_headers),
            {'proxy-authorization': '<proxy-authorization>',
             'authorization': '<authorization>',
             'phone': 'non-secret phone'})


class LogAMQPMessageMiddlewareTestCase(object):

    def test_middleware_returns_unmodified_message(self):
        """[Positive] process doesn't modify input message."""
        message = mock.MagicMock()
        message.headers = {}
        message.body = mock.Mock()

        output = self._middleware.process(message)

        self.assertEqual(output, message)
        self.assertEqual(output.headers, message.headers)
        self.assertEqual(output.body, message.body)


class LogIncomingAMQPMessageMiddlewareTestCase(
        unittest.TestCase, LogAMQPMessageMiddlewareTestCase):

    @mock.patch('logging.getLogger')
    def setUp(self, getLogger):
        super(LogIncomingAMQPMessageMiddlewareTestCase, self).setUp()
        self.log = mock.MagicMock()
        getLogger.return_value = self.log
        self.log.getEffectiveLevel = mock.MagicMock(return_value=logging.DEBUG)
        self._middleware = steps.LogIncomingAMQPMessageMiddleware()

    def test_process_writes_headers_and_body_to_log(self):
        """[Positive] process uses self._log to logging."""

        message = mock.MagicMock()
        message.headers = 'headers'
        message.body = 'body'

        with mock.patch.object(self._middleware,
                               '_hide_sensitive_data',
                               return_value='processed_headers'):
            self._middleware.process(message)

            (self._middleware._hide_sensitive_data
             .assert_called_once_with('headers'))

            self.log.debug.assert_called_once_with(
                'Incoming AMQP message with headers \'%s\' and body \'%s\'',
                'processed_headers',
                'body')


class LogOutgoingAMQPMessageMiddlewareTestCase(
        unittest.TestCase, LogAMQPMessageMiddlewareTestCase):

    @mock.patch('logging.getLogger')
    def setUp(self, getLogger):
        super(LogOutgoingAMQPMessageMiddlewareTestCase, self).setUp()
        self.log = mock.MagicMock()
        getLogger.return_value = self.log
        self.log.getEffectiveLevel = mock.MagicMock(return_value=logging.DEBUG)
        self._middleware = steps.LogOutgoingAMQPMessageMiddleware()

    def test_process_writes_headers_and_body_to_log(self):
        """[Positive] process uses self._log to logging."""

        message = mock.MagicMock()
        message.headers = 'headers'
        message.body = 'body'

        with mock.patch.object(self._middleware,
                               '_hide_sensitive_data',
                               return_value='processed_headers'):
            self._middleware.process(message)

            (self._middleware._hide_sensitive_data
             .assert_called_once_with('headers'))

            self.log.debug.assert_called_once_with(
                'Outgoing AMQP message with headers \'%s\' and body \'%s\'',
                'processed_headers',
                'body')
