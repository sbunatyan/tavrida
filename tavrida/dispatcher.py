#!/usr/bin/env python
# Copyright (c) 2015 Sergey Bunatyan <sergey.bunatyan@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import inspect

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
            "notification": {}
        }

    @property
    def handlers(self):
        return self._handlers

    @property
    def subscriptions(self):
        return self._handlers["notification"]

    def register(self, entry_point, message_type, handler_method_name):
        """
        Registers for given message type and entry_point a handler

        :param entry_point: some Entry point
        :type entry_point: EntryPoint
        :param message_type: type of incoming message
        :type message_type: string
        :param handler_method_name: name of handler method
        :type handler_method_name: string
        """
        ep = str(entry_point)
        if ep in self._handlers[message_type]:
            raise exceptions.DuplicatedEntryPointRegistration(entry_point=ep)
        if handler_method_name in self._handlers[message_type].values():
            raise exceptions.DuplicatedMethodRegistration(
                method_name=handler_method_name)
        self._handlers[message_type][ep] = handler_method_name

    def get_handler(self, entry_point, message_type):
        """
        Return handler that defined for given entry_point and message_type

        :param entry_point: some Entry point
        :type entry_point: EntryPoint
        :param message_type: type of incoming message
        :type message_type: string
        :return:name of handler method
        :rtype: string
        """
        ep = str(entry_point)
        if message_type not in self._handlers or \
                ep not in self._handlers[message_type]:
            raise exceptions.HandlerNotFound(entry_point=str(ep),
                                             message_type=message_type)
        return self._handlers[message_type][ep]

    def get_publishers(self):
        """
        Generates entry points for notifications

        :return: generator of EntryPoints
        """
        for ep in self.subscriptions.keys():
            yield entry_point.EntryPointFactory().create(ep)

    def get_request_entry_services(self):
        """
        Generates entry points for requests

        :return: generator of EntryPoints
        """
        for ep in self._handlers["request"].keys():
            yield entry_point.EntryPointFactory().create(ep).service

    def _get_dispatching_entry_point(self, message):
        """
        Defines by what header message should be dispatched

        :param message: incoming message
        :type message: Message
        :return: corresponding EntryPoint
        :rtype: EntryPoint
        """
        if isinstance(message, (messages.IncomingError,
                                messages.IncomingResponse)):
            return message.source.copy()
        elif isinstance(message, messages.IncomingNotification):
            return message.source
        else:
            return message.destination.copy()

    def _get_source_context(self, message, service_instance):
        """
        Prepares 'source' value for RPC proxy

        :param message: incoming message
        :type message: Message
        :param service_instance: Service controller instance
        :type service_instance: service.ServiceController
        :rtype: EntryPoint
        """
        if isinstance(message, (messages.IncomingError,
                                messages.IncomingResponse)):
            return message.destination
        elif isinstance(message, messages.IncomingNotification):
            return entry_point.EntryPointFactory().create(
                service_instance.service_name)
        else:
            return message.destination

    def _create_rpc_proxy(self, service_instance, message):
        """
        Create RPC proxy to provide it to handler

        :param service_instance: Service controller instance
        :type service_instance: service.ServiceController
        :param message: incoming message
        :type message: messages.Message
        :return: RPCProxy to implement requests
        :rtype: proxies.RPCProxy
        """
        return proxies.RPCProxy(postprocessor=service_instance.postprocessor,
                                source=self._get_source_context(
                                    message, service_instance),
                                context=message.context,
                                correlation_id=message.correlation_id,
                                headers=message.headers)

    def process(self, message, service_instance):
        """
        Finds method to handle request and call service's 'process' method with
        method name, message and RPC proxy

        :param message: incoming message
        :type message: message.Message
        :param service_instance: service
        :type service_instance: services.ServiceController
        :return: service's response
        :rtype: messages.Message, dict, None
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

        cls.service_name = service_name
        for method_name in dir(cls):
            method = getattr(cls, method_name)

            # if method is handler then register it in dispatcher
            if hasattr(method, "_method_name") \
                and hasattr(method, "_service_name") \
                    and hasattr(method, "_method_type"):

                # register service in router to define message controller
                # class
                router.Router().register(method._service_name,
                                         cls)
                ep = entry_point.EntryPoint(method._service_name,
                                            method._method_name)
                cls.get_dispatcher().register(ep,
                                              method._method_type,
                                              method_name)

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
        func._arg_names = inspect.getargspec(func)[0][1:]

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
        func._arg_names = inspect.getargspec(func)[0][1:]

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
        func._arg_names = inspect.getargspec(func)[0][1:]

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
        func._arg_names = inspect.getargspec(func)[0][1:]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
