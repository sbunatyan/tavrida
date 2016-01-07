Proxy
=====

Proxy is the object that allows you to execute calls to remote services and publish notifications.

Each handler gets proxy object as a second parameter.

Proxy parameters
----------------

* You can pass optional *correlation_id* parameter.
If remote service executes the second call to the next service correlation_id will be the same.

* To the *call* or *cast* method you can pass *correlation_id*, *context*, *source* values.

* To the *call* method you can provide *reply_to* parameter.

* You can add header parameter to the proxy using *add_headers* method

.. code-block:: python
    :linenos:

    from tavrida import dispatcher
    from tavrida import service

    @dispatcher.rpc_service("local_service")
    class LocalServiceController(service.ServiceController):

        @dispatcher.rpc_method(service="local_service", method="rpc_method")
        def rpc_method(self, request, proxy, param):
            proxy.remote_service.method(value="call-1").call(correlation_id="123=456)
            proxy.remote_service.method(value="call-1").cast()
            proxy.publish(value="notification_value")
