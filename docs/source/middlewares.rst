Middlewares
===========

Tavrida has two types of middlewares: incoming and outgoing. They are executed just before (after) the handler call.

Middleware is a simple class inherited from :class:`tavrida.middleware.Middleware` that implements a single method :func:`process`

This method takes message and returns the result message for the next middleware.

When you add midlleware it is placed in the list and therefore the addition order is significant.

Incoming Middlewares
--------------------

Example how to add incoming middleware:

.. code-block:: python
    :linenos:

    from tavrida import dispatcher
    from tavrida import middleware
    from tavrida import service

    class MyMiddleware(middleware.Middleware):
        def process(self, message):
            print "middleware call"
            return message

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

        def __init__(self, postprocessor):
            super(self, HelloController).__init__(postprocessor)
            self.add_incoming_middleware(MyMiddleware())

        @dispatcher.rpc_method(service="test_hello", method="hello")
        def handler(self, request, proxy, param):
            return {"parameter": "value"}

By default incoming message takes :class:`tavrida.messages.IncomingRequest`.

Incoming middleware can return 3 type of messages

* If IncomingRequest is returned, it will be passed to the next middleware in the list.
* If Response/Error is returned, the chain of middleware processing is broken and message is returned to the calling service (of course if the incoming message is of type IncomingRequestCall)
* If any other type of response is returned the exception raises.

If exception is raised in middleware it is automatically converted to :class:`tavrida.messages.Error`


Outgoing Middlewares
--------------------

Outgoing middlewares are **NOT** called while executing call via proxy object.


Example how to add outgoing middleware:

.. code-block:: python
    :linenos:

    from tavrida import dispatcher
    from tavrida import middleware
    from tavrida import service

    class MyMiddleware(middleware.Middleware):
        def process(self, message):
            print "middleware call"
            return message

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

        def __init__(self, postprocessor):
            super(self, HelloController).__init__(postprocessor)
            self.add_outgoing_middleware(MyMiddleware())

        @dispatcher.rpc_method(service="test_hello", method="hello")
        def handler(self, request, proxy, param):
            return {"parameter": "value"}

By default outgoing middleware takes Response or Error message.

The result value of outgoing middleware should be of the same type. Otherwise exception is raised.

If exception is raised in outgoing middleware the message processing is stopped.
