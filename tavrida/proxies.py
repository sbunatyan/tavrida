import entry_point
import messages


class RCPCallProxy(object):

    """
    Proxy class for method call
    """

    def __init__(self, postprocessor, service_name, method_name, source,
                 context, correlation_id, kwargs):
        self._postprocessor = postprocessor
        self._service_name = service_name
        self._metohd_name = method_name
        self._source = source
        self._context = context
        self._correlation_id = correlation_id
        self._kwargs = kwargs

    def _make_request(self, context=None, correlation_id=None, reply_to=None,
                      source=None):
        if not source:
            source = self._source

        if not reply_to:
            reply_to = source

        if not context:
            context = self._context

        if not correlation_id:
            correlation_id = self._correlation_id

        payload = self._kwargs
        dst = entry_point.Destination(self._service_name, self._metohd_name)
        request = messages.Request(correlation_id=correlation_id,
                                   reply_to=reply_to,
                                   source=source,
                                   destination=dst,
                                   context=context,
                                   **payload)
        return request

    def call(self, correlation_id=None, context=None, reply_to=None,
             source=None):
        """
        Executes

        :param reply_to:
        :param source:
        :return:
        """
        request = self._make_request(context=context,
                                     correlation_id=correlation_id,
                                     reply_to=reply_to,
                                     source=source)
        self._postprocessor.process(request)

    def cast(self, correlation_id=None, context=None, source=None):
        request = self._make_request(context=context,
                                     correlation_id=correlation_id,
                                     reply_to=entry_point.NullEntryPoint(),
                                     source=source)
        self._postprocessor.process(request)

    def transfer(self, request, context=None, reply_to=None, source=None):
        if request.context:
            context = context or {}
            context.update(request.context)
        request = self._make_request(correlation_id=request.correlation_id,
                                     reply_to=reply_to,
                                     context=context,
                                     source=source)
        self._postprocessor.process(request)


class RPCMethodProxy(object):

    def __init__(self, postprocessor, service_name, method_name, source,
                 context=None, correlation_id=None):
        self._postprocessor = postprocessor
        self._service_name = service_name
        self._method_name = method_name
        self._source = source
        self._context = context
        self._correlation_id = correlation_id

    def __call__(self, **kwargs):
        self._kwargs = kwargs
        return RCPCallProxy(self._postprocessor, self._service_name,
                            self._method_name, self._source, self._context,
                            self._correlation_id, kwargs)


class RPCServiceProxy(object):

    def __init__(self, postprocessor, name, source, context=None,
                 correlation_id=None):
        self._postprocessor = postprocessor
        self._name = name
        self._source = source
        self._context = context
        self._correlation_id = correlation_id

    def __getattr__(self, item):
        return RPCMethodProxy(self._postprocessor, self._name, item,
                              self._source, self._context,
                              self._correlation_id)


class RPCProxy(object):

    def __init__(self, postprocessor, source, context=None,
                 correlation_id=None):
        self._postprocessor = postprocessor
        self._source = source
        self._context = context
        self._correlation_id = correlation_id

    def _get_discovery_service(self):
        return self._postprocessor.discovery_service

    def __getattr__(self, item):
        disc = self._get_discovery_service()
        disc.get_remote(item)
        return RPCServiceProxy(self._postprocessor, item, self._source,
                               self._context, self._correlation_id)

    def publish(self, correlation_id=None, **kwargs):
        publication = messages.Notification(
            correlation_id=correlation_id or self._correlation_id,
            source=self._source,
            context=self._context,
            **kwargs)
        self._postprocessor.process(publication)
