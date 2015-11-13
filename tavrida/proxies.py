import entry_point
import messages


class RCPCallProxy(object):

    """
    Proxy class for method call
    """

    def __init__(self, postprocessor, service_name, method_name, source,
                 context, kwargs):
        self._postprocessor = postprocessor
        self._service_name = service_name
        self._metohd_name = method_name
        self._source = source
        self._context = context
        self._kwargs = kwargs

    def _make_request(self, context=None, request_id=None, reply_to=None,
                      source=None):
        if not source:
            source = self._source

        if not reply_to:
            reply_to = source

        if not context:
            context = self._context

        payload = self._kwargs
        dst = entry_point.Destination(self._service_name, self._metohd_name)
        if not request_id:
            request = messages.Request(reply_to=reply_to,
                                       source=source,
                                       destination=dst,
                                       context=context,
                                       **payload)
        else:
            request = messages.Request.create_transfer(request_id=request_id,
                                                       reply_to=reply_to,
                                                       source=source,
                                                       destination=dst,
                                                       context=context,
                                                       **payload)
        return request

    def call(self, context=None, reply_to=None, source=None):
        """
        Executes

        :param reply_to:
        :param source:
        :return:
        """
        request = self._make_request(context=context, reply_to=reply_to,
                                     source=source)
        self._postprocessor.process(request)

    def cast(self, context=None, source=None):
        if not source:
            source = self._source

        payload = self._kwargs
        dst = entry_point.Destination(self._service_name, self._metohd_name)
        request = messages.Request(reply_to=entry_point.NullEntryPoint(),
                                   source=source,
                                   destination=dst,
                                   context=context,
                                   **payload)
        self._postprocessor.process(request)

    def transfer(self, request, reply_to=None, source=None):
        request = self._make_request(request_id=request.request_id,
                                     reply_to=reply_to,
                                     context=request.context,
                                     source=source)
        return request


class RPCMethodProxy(object):

    def __init__(self, postprocessor, service_name, method_name, source,
                 context=None):
        self._postprocessor = postprocessor
        self._service_name = service_name
        self._method_name = method_name
        self._source = source
        self._context = context

    def __call__(self, **kwargs):
        self._kwargs = kwargs
        return RCPCallProxy(self._postprocessor, self._service_name,
                            self._method_name, self._source, self._context,
                            kwargs)


class RPCServiceProxy(object):

    def __init__(self, postprocessor, name, source, context=None):
        self._postprocessor = postprocessor
        self._name = name
        self._source = source
        self._context = context

    def __getattr__(self, item):
        return RPCMethodProxy(self._postprocessor, self._name, item,
                              self._source, self._context)


class RPCProxy(object):

    def __init__(self, postprocessor, source, context=None):
        self._postprocessor = postprocessor
        self._source = source
        self._context = context

    def _get_discovery_service(self):
        return self._postprocessor.discovery_service

    def __getattr__(self, item):
        disc = self._get_discovery_service()
        disc.get_remote(item)
        return RPCServiceProxy(self._postprocessor, item, self._source,
                               self._context)

    def publish(self, **kwargs):
        publication = messages.Notification(source=self._source,
                                            context=self._context,
                                            **kwargs)
        self._postprocessor.process(publication)
