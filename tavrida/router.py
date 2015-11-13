import controller
import exceptions
import messages

import utils


class Router(utils.Singleton, controller.AbstractController):

    _services = {}
    _subscriptions = {}

    @property
    def services(self):
        return self._services

    @property
    def subscriptions(self):
        return self._subscriptions

    def register(self, service_name, service_cls):
        if service_name in self._services:
            raise exceptions.DuplicatedServiceRegistration(
                service=str(service_cls))
        self._services[service_name] = service_cls

    def register_subscription(self, service_name, service_cls):
        if service_name in self._subscriptions:
            raise exceptions.DuplicatedServiceRegistration(
                service=str(service_cls))
        self._subscriptions[service_name] = service_cls

    def _get_service_cls(self, ep):
        if ep.service not in self._services:
            raise exceptions.ServiceNotFound(entry_point=str(ep))
        return self._services[ep.service]

    def _get_service(self, service_cls, service_list):
        for service in service_list:
            if type(service) == service_cls:
                return service
        raise exceptions.UnknownService(service=str(service_cls))

    def _get_subscription_service_cls(self, ep):
        if ep.service not in self._subscriptions:
            raise exceptions.ServiceNotFound(entry_point=str(ep))
        return self._subscriptions[ep.service]

    def reverse_lookup(self, service_cls):
        for srv_name, srv_cls, in self._services.iteritems():
            if srv_cls == service_cls:
                return srv_name
        raise exceptions.ServiceIsNotRegister(service=str(service_cls))

    def subscription_lookup(self, service_cls):
        for srv_name, srv_cls, in self._subscriptions.iteritems():
            if srv_cls == service_cls:
                return srv_name
        raise exceptions.ServiceIsNotRegister(service=str(service_cls))

    def process(self, message, service_list):
        """
        Return service class that defined for entry_point.
        """
        if isinstance(message, (messages.IncomingError,
                                messages.IncomingResponse)):
            service_cls = self._get_service_cls(message.destination)
        elif isinstance(message, messages.IncomingNotification):
            service_cls = self._get_subscription_service_cls(message.source)
        else:
            service_cls = self._get_service_cls(message.destination)

        service = self._get_service(service_cls, service_list)

        if isinstance(message, messages.IncomingNotification):
            srv_name = self.reverse_lookup(service_cls)
            return service_cls.get_subscription().process(message, srv_name,
                                                          service)
            #return service_cls.get_dispatcher().process(message, service)
        else:
            return service_cls.get_dispatcher().process(message, service)
