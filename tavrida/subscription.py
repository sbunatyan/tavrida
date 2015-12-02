import controller
import exceptions
import proxies


class Subscription(controller.AbstractController):

    """
    Routing class for subscriptions.
    """

    def __init__(self):
        super(Subscription, self).__init__()
        self._subscriptions = {}

    @property
    def subscriptions(self):
        return self._subscriptions

    def subscribe(self, remote_ep, local_ep):
        """
        Subscribe local handler for topic (remote publisher method)

        :param remote_ep: Remote entry point
        :type remote_ep: entry_point.EntryPoint
        :param method_name: Name of handler method
        :type method_name: string
        """
        self._subscriptions[remote_ep.method] = local_ep

    def get_publisher(self, method_name):
        """
        Get remote entry point method by local method name

        :param method_name: Name of handler method
        :type method_name: string
        :return: Remote entry point method name
        :rtype: string
        """
        for ep_method, local_ep in self._subscriptions.iteritems():
            if local_ep.method == method_name:
                return ep_method
        raise exceptions.PublisherEndpointNotFound(method_name=method_name)

    def _get_subscription_entry_point(self, message):
        """
        Defines by what header message should be dispatched

        :param message: IncomingNotification
        :type message: Message
        :return: corresponding EntryPoint
        :rtype: EntryPoint
        """
        return message.source

    def process(self, message, service_instance):
        """
        Calls handler of the corresponding service with given message

        :param message: Message to process
        :type message: messages.Message
        :return: Remote entry point method name
        :rtype: string
        """
        ep = self._get_subscription_entry_point(message)
        local_ep = self.get_handler(ep)
        proxy = self._create_rpc_proxy(service_instance,
                                       local_ep, message)
        return service_instance.process(local_ep.method, message, proxy)

    def get_handler(self, ep):
        """
        Return handlers that defined for entry_point.
        """
        local_ep = self._subscriptions[ep.method]
        return local_ep

    def _create_rpc_proxy(self, service_instance, ep, message):
        return proxies.RPCProxy(postprocessor=service_instance.postprocessor,
                                source=ep,
                                context=message.context,
                                correlation_id=message.correlation_id,
                                headers=message.headers)
