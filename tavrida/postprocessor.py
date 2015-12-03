import logging

import controller
import entry_point
import steps
import utils


class PostProcessor(controller.AbstractController, utils.Singleton):

    """
    Processes outgoing messages. This class is responsible for message
    transfer to writer
    """

    _steps = [
        steps.CreateAMQPMiddleware(),
        steps.ValidateMessageMiddleware(),
    ]

    _middlewares = []

    def __init__(self, driver, discovery):
        super(PostProcessor, self).__init__()
        self.log = logging.getLogger(__name__)
        self._driver = driver
        self._discovery = discovery

    def add_middleware(self, middleware):
        """
        Prepend middleware controller

        :param middleware: middleware object
        :type middleware: middleware.Middleware
        """
        self._middlewares.insert(0, middleware)

    def process(self, message_obj):
        """
        Processes outgoing message

        :param message_obj: message
        :type message_obj: messages.Message
        """
        msg = message_obj
        all_controllers = self._middlewares + self._steps
        for step in all_controllers:
            msg = step.process(msg)
        self._send(msg)

    @property
    def discovery_service(self):
        return self._discovery

    def _send(self, message):
        """
        Sends AMQP message to exchange via writer

        :param message: AMQP message to send
        :type message: messages.AMQPMessage
        :return:
        """
        discovery_service = self.discovery_service
        if message.headers["message_type"] == "notification":
            source = message.headers["source"]
            ep = entry_point.EntryPointFactory().create(source)
            exchange = discovery_service.get_local_publisher(ep.service)
        else:
            dst = message.headers["destination"]
            ep = entry_point.EntryPointFactory().create(dst)
            exchange = discovery_service.get_remote(ep.service)
        routing_key = ep.to_routing_key()
        self._driver.publish_message(exchange, routing_key, message)
