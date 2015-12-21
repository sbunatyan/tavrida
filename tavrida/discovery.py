import abc

import exceptions


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

    _remote_registry = {}
    _remote_publisher_registry = {}
    _local_publisher_registry = {}

    def __init__(self):
        super(LocalDiscovery, self).__init__()

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
            'remote': self._remote_registry.values(),
            'remote_publisher': self._remote_publisher_registry.values(),
            'local_publisher': self._local_publisher_registry.values()
        }
