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
