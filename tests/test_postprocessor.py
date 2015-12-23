import unittest

import mock

from tavrida import entry_point
from tavrida import postprocessor
from tavrida import steps


class PostprocessorTestCase(unittest.TestCase):

    def setUp(self):
        super(PostprocessorTestCase, self).setUp()
        self.driver = mock.MagicMock()
        self.discovery = mock.MagicMock()
        self.postprocessor = postprocessor.PostProcessor(self.driver,
                                                         self.discovery)

    def test_first_two_steps_in_list(self):
        """
        Tests that the first step is CreateAMQPMiddleware and the second is
        ValidateMessageMiddleware
        """

        self.assertIsInstance(self.postprocessor._steps[0],
                              steps.CreateAMQPMiddleware)
        self.assertIsInstance(self.postprocessor._steps[1],
                              steps.ValidateMessageMiddleware)

    @mock.patch.object(postprocessor.PostProcessor, "_send")
    def test_process_runs_middlewares_and_sends_message(self, send_mock):
        """
        Tests all steps are called and finally message is sent
        """
        message = mock.MagicMock()
        first_step = mock.MagicMock()
        self.postprocessor._steps = [first_step]

        self.postprocessor.process(message)
        for step in self.postprocessor._steps:
            step.process.assert_called_once_with(message)
        send_mock.assert_called_once_with(first_step.process())

    @mock.patch.object(entry_point, "EntryPointFactory")
    def test_send_notification(self, ep_factory):
        """
        Tests that notification is sent to notification exchange with routing
        key based on message source
        """

        message = mock.MagicMock()
        message.headers = {
            "message_type": "notification",
            "source": "some_value"
        }
        self.postprocessor._send(message)

        ep_factory().create.assert_called_once_with(message.headers["source"])
        ep = ep_factory().create(message.headers["source"])
        self.discovery.get_local_publisher.assert_called_once_with(ep.service)
        exchange = self.discovery.get_local_publisher(ep.service)
        rk = ep.to_routing_key()
        self.driver.publish_message.assert_called_once_with(exchange, rk,
                                                            message)

    @mock.patch.object(entry_point, "EntryPointFactory")
    def test_send_response(self, ep_factory):
        """
        Tests that response is sent to remote service exchange with routing
        key based on message destination
        """

        message = mock.MagicMock()
        message.headers = {
            "message_type": "response",
            "destination": "some_value"
        }
        self.postprocessor._send(message)

        ep_factory().create.assert_called_once_with(
            message.headers["destination"])
        ep = ep_factory().create(message.headers["destination"])
        self.discovery.get_remote.assert_called_once_with(ep.service)
        exchange = self.discovery.get_remote(ep.service)
        rk = ep.to_routing_key()
        self.driver.publish_message.assert_called_once_with(exchange, rk,
                                                            message)

    @mock.patch.object(entry_point, "EntryPointFactory")
    def test_send_error(self, ep_factory):
        """
        Tests that error is sent to remote service exchange with routing
        key based on message destination
        """

        message = mock.MagicMock()
        message.headers = {
            "message_type": "error",
            "destination": "some_value"
        }
        self.postprocessor._send(message)

        ep_factory().create.assert_called_once_with(
            message.headers["destination"])
        ep = ep_factory().create(message.headers["destination"])
        self.discovery.get_remote.assert_called_once_with(ep.service)
        exchange = self.discovery.get_remote(ep.service)
        rk = ep.to_routing_key()
        self.driver.publish_message.assert_called_once_with(exchange, rk,
                                                            message)

    @mock.patch.object(entry_point, "EntryPointFactory")
    def test_send_request(self, ep_factory):
        """
        Tests that request is sent to remote service exchange with routing
        key based on message destination
        """

        message = mock.MagicMock()
        message.headers = {
            "message_type": "request",
            "destination": "some_value"
        }
        self.postprocessor._send(message)

        ep_factory().create.assert_called_once_with(
            message.headers["destination"])
        ep = ep_factory().create(message.headers["destination"])
        self.discovery.get_remote.assert_called_once_with(ep.service)
        exchange = self.discovery.get_remote(ep.service)
        rk = ep.to_routing_key()
        self.driver.publish_message.assert_called_once_with(exchange, rk,
                                                            message)
