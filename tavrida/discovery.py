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

import exceptions

from tavrida import dsfile


class AbstractDiscovery(object):

    """
    Abstract discovery service
    Discovery service should be able to discover remote services (map
    service name to exchange name), remote publishers (map publisher service
    name to exchange name) and local publishers (map local publisher service
    name to exchange name)
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _register_remote(self, service_name, exchange_name):
        """
        Registers remote service

        :param service_name: remote service name
        :type service_name: string
        :param exchange_name: remote service RPC exchange
        :type exchange_name: string
        """
        pass

    @abc.abstractmethod
    def _register_local_publisher(self, service_name, exchange_name):
        """
        Registers local publisher service

        :param service_name: local publisher service name
        :type service_name: string
        :param exchange_name: local service publication exchange
        :type exchange_name: string
        """
        pass

    @abc.abstractmethod
    def _register_remote_publisher(self, service_name, exchange_name):
        """
        Registers remote publisher service

        :param service_name: remote publisher service name
        :type service_name: string
        :param exchange_name: remote service publication exchange
        :type exchange_name: string
        """
        pass

    def register_remote_service(self, service_name, exchange_name):
        """
        Registers remote service

        :param service_name: remote service name
        :type service_name: string
        :param exchange_name: remote service RPC exchange
        :type exchange_name: string
        """
        return self._register_remote(service_name, exchange_name)

    def register_remote_publisher(self, service_name, exchange_name):
        """
        Registers local publisher service

        :param service_name: local publisher service name
        :type service_name: string
        :param exchange_name: local service publication exchange
        :type exchange_name: string
        """
        return self._register_remote_publisher(service_name, exchange_name)

    def register_local_publisher(self, service_name, exchange_name):
        """
        Registers remote publisher service

        :param service_name: remote publisher service name
        :type service_name: string
        :param exchange_name: remote service publication exchange
        :type exchange_name: string
        """
        return self._register_local_publisher(service_name, exchange_name)

    @abc.abstractmethod
    def get_remote(self, service_name):
        """
        Gets remote service

        :param service_name: remote service name
        :type service_name: string
        :return: exchange name
        :rtype: string
        """
        pass

    @abc.abstractmethod
    def get_remote_publisher(self, service_name):
        """
        Gets remote publisher service

        :param service_name: remote service name
        :type service_name: string
        :return: exchange name
        :rtype: string
        """
        pass

    @abc.abstractmethod
    def get_local_publisher(self, service_name):
        """
        Gets local publisher service

        :param service_name: local service name
        :type service_name: string
        :return: exchange name
        :rtype: string
        """
        pass

    @abc.abstractmethod
    def get_all_exchanges(self):
        """
        Gets all exchanges

        :return: dictionary of {'remote': .., 'remote_publisher': ..
                                'local_publisher': ..}
        :rtype: dictionary
        """
        pass


class LocalDiscovery(AbstractDiscovery):

    def __init__(self):
        super(LocalDiscovery, self).__init__()
        self._remote_registry = {}
        self._remote_publisher_registry = {}
        self._local_publisher_registry = {}

    def _register_remote(self, service_name, exchange_name):
        self._remote_registry[service_name] = exchange_name

    def _register_remote_publisher(self, service_name, exchange_name):
        self._remote_publisher_registry[service_name] = exchange_name

    def _register_local_publisher(self, service_name, exchange_name):
        self._local_publisher_registry[service_name] = exchange_name

    def unregister_remote_service(self, service_name):
        del self._remote_registry[service_name]

    def unregister_remote_publisher(self, service_name):
        del self._remote_publisher_registry[service_name]

    def unregister_local_publisher(self, service_name):
        del self._local_publisher_registry[service_name]

    def get_remote(self, service_name):
        if service_name not in self._remote_registry:
            raise exceptions.UnableToDiscover(service=service_name)
        return self._remote_registry[service_name]

    def get_remote_publisher(self, service_name):
        if service_name not in self._remote_publisher_registry:
            raise exceptions.UnableToDiscover(service=service_name)
        return self._remote_publisher_registry[service_name]

    def get_local_publisher(self, service_name):
        if service_name not in self._local_publisher_registry:
            raise exceptions.UnableToDiscover(service=service_name)
        return self._local_publisher_registry[service_name]

    def get_all_exchanges(self):
        return {
            'remote': list(set(self._remote_registry.values())),
            'remote_publisher': list(set(
                self._remote_publisher_registry.values())),
            'local_publisher': list(set(
                self._local_publisher_registry.values()))
        }


class FileBasedDiscoveryService(LocalDiscovery):
    """Discovery service gets own configuration from DSFile

    How to use:

        disc = discovery.FileBasedDiscoveryService(
            "ds.ini",
            "service2",
            subsriptions=["service1"])

    ds.ini:
        [service1]
        exchange=service1_exchange
        notifications=service1_notifications

        [service2]
        exchange=service2_exchange
    """

    def __init__(self,
                 ds_filename,
                 service_name,
                 subscriptions=None):
        """Construct Discovery Service

        Raises exceptions.ServiceIsNotRegister if
           1) ds_filename file doesn't contain service_name
           2) ds_filename file doesn't contain any subsciption
              from subscriptions

        Raises exceptions.CantRegisterRemotePublisher if you try to
        subscribe to service without notifications exchange.

        :param ds_filename: .ds file path
        :type ds_filename: string
        :param service_name: local service name
        :type service_name: string
        :param subscriptions: list of services' names to subscribe to
        :type subscriptions: list of strings
        """
        super(FileBasedDiscoveryService, self).__init__()

        self._service_name = service_name
        subscriptions = set(subscriptions or [])

        dsf = dsfile.DSFile(ds_filename)
        all_services_set = set(dsf)

        # Check subscriptions list
        for subscription in subscriptions:
            if subscription not in all_services_set:
                raise exceptions.ServiceIsNotRegister(service=subscription)

        # If dsf doesn't contain record for service_name will raise
        # KeyError exception. Raise ServiceIsNotRegistered instead of.
        try:
            local_service = dsf[service_name]
        except KeyError as e:
            raise exceptions.ServiceIsNotRegister(service=str(e))

        self._service_exchange = local_service.service_exchange

        # Configure discovery service using dsf.

        # If this service sends notifications register local publisher
        if local_service.notifications_exchange:
            self.register_local_publisher(
                self._service_name,
                local_service.notifications_exchange)

        # Register all services from dsf (excluding service_name) as a
        # remote services
        remote_services = all_services_set - {service_name}

        for remote_service_name in remote_services:
            remote_service = dsf[remote_service_name]
            self.register_remote_service(remote_service.service_name,
                                         remote_service.service_exchange)
            # Subscribe to remote_service notifications.
            if remote_service_name in subscriptions:
                if not remote_service.notifications_exchange:
                    raise exceptions.CantRegisterRemotePublisher(
                        service=remote_service_name)
                self.register_remote_publisher(
                    remote_service.service_name,
                    remote_service.notifications_exchange)

    @property
    def service_name(self):
        return self._service_name

    @property
    def service_exchange(self):
        return self._service_exchange


class DiscoveryFactory(object):

    """
    Discovery factory creates discovery service instances depending on the
    path/url to the discovery service
    """

    def __init__(self, path=None):
        self._path = path

    def get_local_ds(self):
        """
        Returns local discovery instance

        :return: local discovery instance
        :rtype: LocalDiscovery
        """
        return LocalDiscovery()

    def get_file_ds(self, service_name, subscriptions):
        """
        Returns file based discovery instance

        :param service_name: local service name
        :type service_name: string
        :param subscriptions: list of services' names to subscribe to
        :type subscriptions: list of strings
        :return: file based discovery instance
        :rtype: FileBasedDiscoveryService
        """
        return FileBasedDiscoveryService(self._path, service_name,
                                         subscriptions)

    def get_discovery_service(self, service_name=None, subscriptions=None):
        """
        Returns appropriate discovery service instance

        :param service_name: local service name
        :type service_name: string
        :param subscriptions: list of services' names to subscribe to
        :type subscriptions: list of strings
        :return: appropriate discovery service instance
        :rtype: AbstractDiscovery
        """
        if not self._path:
            return self.get_local_ds()
        else:
            return self.get_file_ds(service_name, subscriptions)
