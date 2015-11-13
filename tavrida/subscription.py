import controller
import entry_point
import exceptions
import proxies


class Subscription(controller.AbstractController):

    def __init__(self):
        self._subscriptions = {}

    @property
    def subscriptions(self):
        return self._subscriptions

    def subscribe(self, remote_ep, method_name):
        self._subscriptions[remote_ep.method] = method_name

    def get_publisher(self, method_name):
        for ep_method, method in self._subscriptions:
            if method == method_name:
                return ep_method
        raise exceptions.PublisherEndpointNotFound(method_name=method_name)

    def process(self, message, service_name, service_instance):
        method_name = self.get_handler(message.source)
        ep = entry_point.EntryPoint(service_name, method_name)
        proxy = self._create_rpc_proxy(service_instance, ep)
        return service_instance.process(method_name, message, proxy)

    def get_handler(self, ep):
        """
        Return handlers that defined for entry_point.
        """
        method_name = self._subscriptions[ep.method]
        return method_name

    def _create_rpc_proxy(self, service_instance, ep):
        return proxies.RPCProxy(service_instance.postprocessor, ep)
