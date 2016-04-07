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

import abc
import copy
import logging

import controller
import dispatcher
import exceptions
import messages


class ServiceController(controller.AbstractController):

    """
    Base service controller. All service controllers should be inherited from
    this class.
    This class is responsible for final message processing: calls incoming
    middlewares, calls handler method, after handling calls outgoing
    middlewares and finally sends result to postprocessor.
    """

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

    def send_heartbeat(self):
        self.postprocessor.driver.send_heartbeat_via_reader()

    def _run_outgoing_middlewares(self, result):
        for mld in self._outgoing_middlewares:
            result = mld.process(result)
            if not (isinstance(result, messages.Outgoing)
                    and isinstance(result, messages.Message)):
                raise exceptions.IncorrectOutgoingMessage(message=result)
        return result

    def _send(self, message):
        return self.postprocessor.process(message)

    def _filter_redundant_parameters(self, method_name, incoming_kwargs):
        arg_names = getattr(self, method_name)._arg_names[2:]
        incoming_params = incoming_kwargs.keys()
        if set(arg_names) - set(incoming_params):
            raise ValueError("Wrong incoming parameters (%s) for method '%s'"
                             % (str(incoming_kwargs), method_name))
        else:
            return dict((k, v) for (k, v) in incoming_kwargs.iteritems()
                        if k in arg_names)

    def _handle_request(self, method, request, proxy):
        """
        Calls processor for Request message, gets result and handles exceptions

        :param request: incoming request
        :type request: IncomingRequestCall or IncomingRequestCast
        :return: response or None
        :rtype: messages.Response, messages.Error, None
        """
        try:
            filtered_kwargs = self._filter_redundant_parameters(
                method, request.payload)
            result = getattr(self, method)(request, proxy, **filtered_kwargs)
            if isinstance(request, messages.IncomingRequestCall):
                return result
        except Exception as e:
            if isinstance(request, messages.IncomingRequestCall):
                self.log.exception(e)
                return messages.Error.create_by_request(request, exception=e)
            else:
                raise

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
            try:
                res = mld.process(res)
            except Exception as e:
                if isinstance(message, messages.IncomingRequestCall):
                    res = messages.Error.create_by_request(message, e)

            if not isinstance(res, (messages.Response, messages.Error,
                                    messages.IncomingRequest)):
                raise exceptions.IncorrectMessage(message=res)

            if isinstance(res, (messages.Response, messages.Error)):
                continue_processing = False

                if isinstance(message, messages.IncomingRequestCall):
                    self._send(res)
                break
        return continue_processing, res

    def process(self, method, message, proxy):
        """
        Processes message to corresponding handler.
        Before handler call message is transfered to all middlewares.

        :param method: handler method name
        :type method: string
        :param message: incoming message
        :type message: messages.Message
        :param proxy: proxy to make calls to remote services
        :type proxy: proxies.RPCProxy
        """

        continue_processing, res = self._run_incoming_middlewares(message)
        if continue_processing:
            self._route_message_by_type(method, res, proxy)
