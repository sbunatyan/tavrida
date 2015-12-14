import copy
import logging

import controller
import exceptions
import messages
import steps


class PreProcessor(controller.AbstractController):

    """
    Preprocesses incoming messages. This class is responsible for message
    transfer to processor
    """

    def __init__(self, processor, postprocessor):
        super(PreProcessor, self).__init__()
        self.log = logging.getLogger(__name__)
        self._processor = processor
        self._postprocessor = postprocessor
        self._middlewares = []
        self._steps = [
            steps.ValidateMessageMiddleware(),
            steps.CreateMessageMiddleware()
        ]

    @property
    def processor(self):
        return self._processor

    @property
    def postprocessor(self):
        return self._postprocessor

    def add_middleware(self, middleware):
        """
        Append middleware controller

        :param middleware: middleware object
        :type middleware: middleware.Middleware
        """
        self._middlewares.append(middleware)

    def process(self, amqp_message):
        """
        PreProcesses incoming message

        :param amqp_message: AMPQ message
        :type amqp_message: messages.AMQPMEssage
        :return: response object ot None
        :rtype: Response, Error or None
        """
        msg = amqp_message
        all_controllers = self._steps + self._middlewares
        for step in all_controllers:
            msg = step.process(msg)
            if isinstance(msg, (messages.Response, messages.Error)):
                return self._postprocessor.process(msg)
        return self._route_message_by_type(msg)

    def _route_message_by_type(self, msg):
        msg.update_context(copy.copy(msg.payload))
        if isinstance(msg, messages.IncomingRequest):
            return self._process_request(msg)
        if isinstance(msg, messages.IncomingResponse):
            return self._process_response(msg)
        if isinstance(msg, messages.IncomingNotification):
            return self._process_notification(msg)
        if isinstance(msg, messages.IncomingError):
            return self._process_error(msg)

    def _send(self, message):
        return self._postprocessor.process(message)

    def _handle_request(self, request):
        """
        Calls processor for Request message, gets result and handles exceptions

        :param request: incoming request
        :type request: IncomingRequestCall or IncomingRequestCast
        :return: response or None
        :rtype: messages.Response, messages.Error, None
        """
        try:
            result = self._processor.process(request)
            if isinstance(request, messages.IncomingRequestCall):
                return result
        except Exception as e:
            self.log.exception(e)
            if not isinstance(e, exceptions.BaseAckableException):
                e = exceptions.BaseException()
            if isinstance(request, messages.IncomingRequestCall):
                return messages.Error.create_by_request(request, exception=e)

    def _process_request(self, request):
        """
        Handles Request message and sends back results of controller
        execution if there are any.

        :param request: incoming request
        :type request: IncomingRequestCall or IncomingRequestCast
        """
        result = self._handle_request(request)
        if result:
            if isinstance(result, (messages.Response, messages.Error)):
                self._send(result)
            elif isinstance(result, dict):
                message = request.make_response(**result)
                self._send(message)
            else:
                raise exceptions.WrongResponse(response=str(result))

    def _process_notification(self, notification):
        """
        Handles incoming notification message
        """
        self._processor.process(notification)

    def _process_response(self, response):
        """
        Handles incoming response message
        """
        self._processor.process(response)

    def _process_error(self, error):
        """
        Handles incoming error message
        """
        self._processor.process(error)
