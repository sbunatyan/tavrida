import abc
import copy
import logging

import controller
import dispatcher
import exceptions
import messages


class ServiceController(controller.AbstractController):

    __metaclass__ = abc.ABCMeta

    _dispatcher = None
    _discovery = None

    def __init__(self, postprocessor):
        super(ServiceController, self).__init__()
        self.postprocessor = postprocessor
        self._incoming_middlewares = []
        self._outgoing_middlewares = []
        self.log = logging.getLogger(__name__)

    @classmethod
    def get_discovery(cls):
        if not cls._discovery:
            raise ValueError("Discovery should be defined for service")
        return cls._discovery

    @classmethod
    def set_discovery(cls, discovery):
        cls._discovery = discovery

    @classmethod
    def get_dispatcher(cls):
        if not cls._dispatcher:
            cls._dispatcher = dispatcher.Dispatcher()
        return cls._dispatcher

    def add_incoming_middleware(self, middleware):
        """
        Append middleware controller

        :param middleware: middleware object
        :type middleware: middleware.Middleware
        """
        self._incoming_middlewares.append(middleware)

    def add_outgoing_middleware(self, middleware):
        """
        Append middleware controller

        :param middleware: middleware object
        :type middleware: middleware.Middleware
        """
        self._outgoing_middlewares.append(middleware)

    def _run_outgoing_middlewares(self, result):
        for mld in self._outgoing_middlewares:
            result = mld.process(result)
        return result

    def _send(self, message):
        return self.postprocessor.process(message)

    def _handle_request(self, method, request, proxy):
        """
        Calls processor for Request message, gets result and handles exceptions

        :param request: incoming request
        :type request: IncomingRequestCall or IncomingRequestCast
        :return: response or None
        :rtype: messages.Response, messages.Error, None
        """
        try:
            result = getattr(self, method)(request, proxy, **request.payload)
            if isinstance(request, messages.IncomingRequestCall):
                return result
        except Exception as e:
            self.log.exception(e)
            if not isinstance(e, exceptions.BaseAckableException):
                e = exceptions.BaseException()
            if isinstance(request, messages.IncomingRequestCall):
                return messages.Error.create_by_request(request, exception=e)

    def _process_request(self, method, request, proxy):
        """
        Handles Request message and sends back results of controller
        execution if there are any.

        :param request: incoming request
        :type request: IncomingRequestCall or IncomingRequestCast
        """
        result = self._handle_request(method, request, proxy)
        if result:
            if isinstance(result, (messages.Response, messages.Error)):
                result = self._run_outgoing_middlewares(result)
                self._send(result)
            elif isinstance(result, dict):
                message = request.make_response(**result)
                message = self._run_outgoing_middlewares(message)
                self._send(message)
            else:
                raise exceptions.WrongResponse(response=str(result))

    def _process_notification(self, method, notification, proxy):
        """
        Handles incoming notification message
        """
        getattr(self, method)(notification, proxy, **notification.payload)

    def _process_response(self, method, response, proxy):
        """
        Handles incoming response message
        """
        getattr(self, method)(response, proxy, **response.payload)

    def _process_error(self, method, error, proxy):
        """
        Handles incoming error message
        """
        getattr(self, method)(error, proxy)

    def _route_message_by_type(self, method, message, proxy):
        message.update_context(copy.copy(message.payload))
        if isinstance(message, messages.IncomingRequest):
            return self._process_request(method, message, proxy)
        if isinstance(message, messages.IncomingResponse):
            return self._process_response(method, message, proxy)
        if isinstance(message, messages.IncomingNotification):
            return self._process_notification(method, message, proxy)
        if isinstance(message, messages.IncomingError):
            return self._process_error(method, message, proxy)

    def _run_incoming_middlewares(self, message):
        continue_processing = True
        res = message
        for mld in self._incoming_middlewares:
            res = mld.process(res)

            if isinstance(res, (messages.Response, messages.Error)):
                continue_processing = False

                if isinstance(message, messages.IncomingRequestCall):
                    self._send(res)
                break
        return continue_processing, res

    def process(self, method, message, proxy):

        continue_processing, res = self._run_incoming_middlewares(message)
        if continue_processing:
            self._route_message_by_type(method, res, proxy)
