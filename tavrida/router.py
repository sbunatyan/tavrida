import controller
import entry_point
import exceptions
import messages

import utils


class Router(utils.Singleton, controller.AbstractController):

    _services = []
    _subscriptions = []

    @property
    def services(self):
        return self._services

    @property
    def subscriptions(self):
        return self._subscriptions

    def register(self, service_name, service_cls):
        ep = entry_point.ServiceEntryPoint(service_name)
        try:
            self._get_rpc_service_cls(ep)
        except exceptions.ServiceNotFound:
            self._services.append({service_name: service_cls})

    def register_subscription(self, service_name, service_cls):
        ep = entry_point.ServiceEntryPoint(service_name)
        try:
            self._get_subscription_service_cls(ep)
        except exceptions.ServiceNotFound:
            self._subscriptions.append({service_name: service_cls})

    def _get_rpc_service_cls(self, ep):
        for rpc_mapping in self._services:
            if ep.service in rpc_mapping:
                return rpc_mapping[ep.service]
        raise exceptions.ServiceNotFound(entry_point=str(ep))

    def _get_service(self, service_cls, service_list):
        for service in service_list:
            if type(service) == service_cls:
                return service
        raise exceptions.UnknownService(service=str(service_cls))

    def _get_subscription_service_cls(self, ep):
        for subscription_mapping in self._subscriptions:
            if ep.service in subscription_mapping:
                return subscription_mapping[ep.service]
        raise exceptions.ServiceNotFound(entry_point=str(ep))

    def reverse_lookup(self, service_cls):
        for rpc_mapping in self._services:
            for srv_name, srv_cls, in rpc_mapping.iteritems():
                if srv_cls == service_cls:
                    return srv_name
        raise exceptions.ServiceIsNotRegister(service=str(service_cls))

    def subscription_lookup(self, service_cls):
        for subscription_mapping in self._subscriptions:
            for srv_name, srv_cls, in subscription_mapping.iteritems():
                if srv_cls == service_cls:
                    return srv_name
        raise exceptions.ServiceIsNotRegister(service=str(service_cls))

    def get_service_cls(self, message):
        if isinstance(message, (messages.IncomingError,
                                messages.IncomingResponse)):
            service_cls = self._get_rpc_service_cls(message.destination)
        elif isinstance(message, messages.IncomingNotification):
            service_cls = self._get_subscription_service_cls(message.source)
        else:
            service_cls = self._get_rpc_service_cls(message.destination)
        return service_cls

    def process(self, message, service_list):
        """
        Return service class that defined for entry_point.
        """
        service_cls = self.get_service_cls(message)
        service = self._get_service(service_cls, service_list)

        if isinstance(message, messages.IncomingNotification):
            return service_cls.get_subscription().process(message, service)
        else:
            return service_cls.get_dispatcher().process(message, service)
