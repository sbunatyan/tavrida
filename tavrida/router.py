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

import controller
import exceptions
import messages

import utils


class Router(utils.Singleton, controller.AbstractController):

    _services = []

    @property
    def services(self):
        return self._services

    def register(self, service_name, service_cls):
        """
        Registers Service class for given service name

        :param service_name: name if service
        :type service_name: string
        :param service class:
        :type service_cls: service.ServiceController
        :return:
        """
        ep_maps = set(tuple(ep_map.items()[0]) for ep_map in self._services)
        if not (service_name, service_cls) in ep_maps:
            self._services.append({service_name: service_cls})

    def _check_if_request_suits(self, message, rpc_mapping):
        return message.destination.service in rpc_mapping

    def _check_if_response_suits(self, message, rpc_mapping):
        dst_service = message.destination.service
        src_service = message.source.service
        return (src_service in rpc_mapping and
                dst_service == rpc_mapping[src_service].service_name)

    def get_rpc_service_cls(self, message):

        """
        Returns list of classes that are registered as handlers for message

        :param message: incoming message
        :type message: message.Message
        :return: service class
        :rtype: service.ServiceController
        :raises: DuplicatedServiceRegistration, ServiceNotFound
        """
        # find service classes in mappings ep -> srv_cls
        service_classes = []
        if isinstance(message, (messages.IncomingError,
                                messages.IncomingResponse)):
            ep = message.source
            for rpc_mapping in self._services:
                if self._check_if_response_suits(message, rpc_mapping):
                    service_classes.append(rpc_mapping[message.source.service])
        else:
            ep = message.destination
            for rpc_mapping in self._services:
                if self._check_if_request_suits(message, rpc_mapping):
                    service_classes.append(rpc_mapping[ep.service])

        if len(service_classes) > 1:
            raise exceptions.DuplicatedServiceRegistration(service=ep.service)
        elif len(service_classes) == 0:
            raise exceptions.ServiceNotFound(entry_point=str(ep))
        else:
            return service_classes[0]

    def get_subscription_cls(self, message):
        """
        Returns list of classes that have subscriptions for message source

        :param message: incoming message
        :type message: message.Message
        :return: list of service classes
        :rtype: list
        """

        ep = message.source
        # find service classes in mappings ep -> srv_cls
        service_classes = []
        for rpc_mapping in self._services:
            if ep.service in rpc_mapping:
                service_classes.append(rpc_mapping[ep.service])
        return service_classes

    def _get_service(self, service_cls, service_list):
        for service in service_list:
            if type(service) == service_cls:
                return service
        raise exceptions.UnknownService(service=str(service_cls))

    def reverse_lookup(self, service_cls):
        """
        Returns name of entry point service for which given class is registered

        :param service_cls: service handler class
        :type: service.ServiceController
        :return: name of service
        :rtype: string
        """
        registered = False
        for rpc_mapping in self._services:
            for srv_name, srv_cls, in rpc_mapping.iteritems():
                if srv_cls == service_cls:
                    registered = True
                    yield srv_name
        if not registered:
            raise exceptions.ServiceIsNotRegister(service=str(service_cls))

    def _process_rpc(self, message, service_cls, service_list):
        service = self._get_service(service_cls, service_list)
        return service_cls.get_dispatcher().process(message, service)

    def _process_subscription(self, message, service_classes, service_list):
        for service_cls in service_classes:
            service = self._get_service(service_cls, service_list)
            service_cls.get_dispatcher().process(message, service)

    def process(self, message, service_list):
        """
        Processes message for some service from service list to corresponding
        dispatcher

        :param message: incoming message
        :type message: message.Message
        :param service_list: list of services.ServiceController objects
        :type service_list: list
        :return: messages.Message, dict, None
        """
        if isinstance(message, messages.IncomingNotification):
            service_classes = self.get_subscription_cls(message)
            self._process_subscription(message, service_classes, service_list)
        else:
            service_cls = self.get_rpc_service_cls(message)
            return self._process_rpc(message, service_cls, service_list)
