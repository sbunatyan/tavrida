import functools

import controller
import entry_point
import exceptions
import messages
import proxies
import router


class Dispatcher(controller.AbstractController):

    """
    Dispatches incoming requests to the handler method in class.
    Dispatcher is the class property for each service controller.
    In that class ii find handler method to handle request.
    """

    def __init__(self):

        self._handlers = {
            "request": {},
            "response": {},
            "error": {},
        }

    @property
    def handlers(self):
        return self._handlers

    def register(self, entry_point, message_type, method_name):
        """
        Registers for given message type and entry_point a handler

        :param entry_point: any EntryPoint object
        :type entry_point: EntryPoint
        :param message_type: type of incoming message
        :type message_type: string
        :param method_name: name of handler method
        :type method_name: string
        """
        if entry_point.method in self._handlers[message_type]:
            raise exceptions.DuplicatedEntryPointRegistration(
                method=str(entry_point))
        if method_name in self._handlers[message_type].values():
            raise exceptions.DuplicatedMethodRegistration(
                str(entry_point.method))
        self._handlers[message_type][entry_point.method] = method_name

    def get_handler(self, ep, message_type):
        """
        Return handler that defined for given entry_point and message_type

        :param ep: any EntryPoint object
        :type ep: EntryPoint
        :param message_type: type of incoming message
        :type message_type: string
        :return:name of handler method
        :rtype: string
        """
        if message_type not in self._handlers or \
           ep.method not in self._handlers[message_type]:
            raise exceptions.HandlerNotFound(entry_point=str(ep),
                                             message_type=message_type)
        method_name = self._handlers[message_type][ep.method]
        return method_name

    def _get_dispatching_entry_point(self, message):
        """
        Defines by what header message should be dispatched

        :param message: IncomingRequest, IncomingError, IncomingResponse,
                        IncomingNotification
        :type message: Message
        :return: corresponding EntryPoint
        :rtype: EntryPoint
        """
        if isinstance(message, messages.IncomingError):
            return message.destination
        elif isinstance(message, messages.IncomingResponse):
            return message.destination
        else:
            return message.destination

    def _create_rpc_proxy(self, service_instance, message):
        """
        Create RPC proxy to provide it to handler

        :param service_instance: Service controller instance
        :type service_instance: service.ServiceController
        :param ep: Source entry point
        :type ep: entry_point.EntryPoint (or it's descendants)
        :param message: message
        :type message: messages.Message
        :return: RPCProxy to implement requests
        :rtype: proxies.RPCProxy
        """
        return proxies.RPCProxy(postprocessor=service_instance.postprocessor,
                                source=message.destination,
                                context=message.context,
                                correlation_id=message.correlation_id,
                                headers=message.headers)

    def process(self, message, service_instance):
        """
        Finds method to handle request and call service's 'process' method with
        method name, message and RPC proxy

        :param message: Message (Request, Response, Error, Notification)
        :type message: message.Message
        :param service_instance:
        :type service_instance:
        :return: service's response
        :rtype: Message, dict, None
        """
        ep = self._get_dispatching_entry_point(message)
        method_name = self.get_handler(ep, message.type)
        proxy = self._create_rpc_proxy(service_instance, message)
        return service_instance.process(method_name, message, proxy)


def rpc_service(service_name):
    """
    Decorator that registers service in dispatcher, router and subscription
    (the last - for notifications only)

    :param service_name: name of service
    :type service_name: string
    :return: service class wrapper
    :rtype: function
    """
    def decorator(cls):
        import service
        if not issubclass(cls, service.ServiceController):
            raise exceptions.NeedToBeController(service=str(cls))

        for method_name in dir(cls):
            method = getattr(cls, method_name)

            # if method is handler then register it in dispatcher
            if hasattr(method, "_method_name") \
                and hasattr(method, "_service_name") \
                    and hasattr(method, "_method_type"):

                if method._method_type != "notification":

                    # register service in router to define message controller
                    # class
                    router.Router().register(method._service_name,
                                             cls)
                    ep = entry_point.EntryPoint(method._service_name,
                                                method._method_name)
                    cls.get_dispatcher().register(ep,
                                                  method._method_type,
                                                  method_name)

                # if method subscribes on notifications register publisher
                # entry point in router and in subscription
                else:
                    router.Router().register_subscription(method._service_name,
                                                          cls)
                    ep = entry_point.EntryPoint(method._service_name,
                                                method._method_name)
                    cls.get_subscription().subscribe(
                        ep, entry_point.Source(service_name, method_name))
        return cls
    return decorator


def rpc_method(service, method):
    """
    Decorator that registers method as PRC handler in service controller

    :param method: Name of entry point method to handle
    :type method: string
    :return: decorator
    :rtype: function
    """

    def decorator(func):
        func._service_name = service
        func._method_name = method
        func._method_type = "request"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rpc_response_method(service, method):
    """
    Decorator that registers method as PRC response handler in service
    controller

    :param method: Name of entry point method to handle (remote method)
    :type method: string
    :return: decorator
    :rtype: function
    """
    def decorator(func):
        func._service_name = service
        func._method_name = method
        func._method_type = "response"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rpc_error_method(service, method):
    """
    Decorator that registers method as PRC error handler in service
    controller

    :param method: Name of entry point method to handle (remote method)
    :type method: string
    :return: decorator
    :rtype: function
    """
    def decorator(func):
        func._service_name = service
        func._method_name = method
        func._method_type = "error"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def subscription_method(service, method):
    """
    Decorator that registers method as subscription handler in service
    controller

    :param service: Name of remote service to subscribe
    :type service: string
    :param method: Name of event (remote method name)
    :type method: string
    :return: decorator
    :rtype: function
    """
    def decorator(func):
        func._service_name = service
        func._method_name = method
        func._method_type = "notification"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
