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
        ep_maps = set(tuple(ep_map.items()[0]) for ep_map in self._services)
        if not (service_name, service_cls) in ep_maps:
            self._services.append({service_name: service_cls})

    def _check_if_request_suits(self, ep, rpc_mapping):
        return ep.service in rpc_mapping

    def check_if_response_suits(self, ep, rpc_mapping, source_srv_name):
        return (ep.service in rpc_mapping and
                source_srv_name == rpc_mapping[ep.service].service_name)

    def get_rpc_service_cls(self, message):

        ep = message.destination
        source_srv_name = message.source.service

        # find service classes in mappings ep -> srv_cls
        service_classes = []
        if isinstance(message, (messages.IncomingError,
                                messages.IncomingResponse)):
            for rpc_mapping in self._services:
                if self.check_if_response_suits(ep, rpc_mapping,
                                                source_srv_name):
                    service_classes.append(rpc_mapping[ep.service])
        else:
            for rpc_mapping in self._services:
                if self._check_if_request_suits(ep, rpc_mapping):
                    service_classes.append(rpc_mapping[ep.service])

        if len(service_classes) > 1:
            raise exceptions.DuplicatedServiceRegistration(service=ep.service)
        elif len(service_classes) == 0:
            raise exceptions.ServiceNotFound(entry_point=str(ep))
        else:
            return service_classes[0]

    def get_subscription_cls(self, message):
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
        Return service class that defined for entry_point.
        """
        if isinstance(message, messages.IncomingNotification):
            service_classes = self.get_subscription_cls(message)
            self._process_subscription(message, service_classes, service_list)
        else:
            service_cls = self.get_rpc_service_cls(message)
            return self._process_rpc(message, service_cls, service_list)
