Controller
==========

Controller class
----------------

To declare controller class you should inherit it
from :class:`tavrida.service.ServiceController` and
decorate with :func:`tavrida.dispatcher.rpc_service` decorator

.. code-block:: python
    :linenos:

    from tavrida import dispatcher
    from tavrida import service

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):
        pass

Request handler can return 2 type of responses (dict, :class:`tavrida.messages.Response`, :class:`tavrida.messages.Error`) or None value.

If dict is returned it will be converted to the :class:`tavrida.messages.Response` object.
If any exception raises during message processing it is converted to :class:`tavrida.messages.Error` object.

But you can, of course, return :class:`tavrida.messages.Response` or :class:`tavrida.messages.Error` object explicitly.

Controller is instantiated on :class:`tavrida.server.Server` start.
Each service controller class owns a :class:`tavrida.dispatcher.Dispatcher` and discovery object.

If you are planning to execute calls from any of the handlers you should bind discovery object to the service class before :class:`tavrida.server.Server` starts.

.. code-block:: python
    :linenos:

    disc.register_remote_service("remote_service", "remote_service_exchange")
    HelloController.set_discovery(disc)


Handlers
--------

Handlers are methods of service controllers that are called on message (
:class:`tavrida.messages.IncomingRequest` request,
:class:`tavrida.messages.IncomingResponse` response,
:class:`tavrida.messages.IncomingError` error,
:class:`tavrida.messages.IncomingNotification` notification) arrival.

Each handler is bound to :class:`tavrida.entry_point.EntryPoint` which can be considered as an address to deliver the message.

Each handler receives two parameters (at first two positions): message and :class:`tavrida.proxies.RPCProxy`.
Class of incoming message depends on handler type. Using :class:`tavrida.proxies.RPCProxy` object you
can execute calls to remote services.
In such calls the service's discovery object is used.

All following parameters are custom parameters of a particular method.
In the following example *param* is such parameter.

Request handler
+++++++++++++++

:class:`tavrida.messages.IncomingRequest` routing is based on the name of local service entry point.
For example for *test_hello* service the correct entry point service value is *test_hello*

.. code-block:: python
    :linenos:

    @dispatcher.rpc_method(service="test_hello", method="hello")
    def handler(self, request, proxy, param):
        return {"parameter": "value"}


Response handler
++++++++++++++++

:class:`tavrida.messages.IncomingResponse` routing is based on the name of remote service entry point.
For example for *test_hello* service and remote entry point *remote_service.remote_method* the correct entry point value is *remote_service.remote_method*

.. code-block:: python
    :linenos:

    @dispatcher.rpc_response_method(service="remote_service", method="remote_method")
    def world_resp(self, response, proxy, param):
        pass

Error handler
+++++++++++++

:class:`tavrida.messages.IncomingError` routing is based on the name of remote service entry point.
For example for *test_hello* service and remote entry point *remote_service.remote_method* the correct entry point value is *remote_service.remote_method*
Error handler takes strictly **two** parameters.
The first (error) parameter has a property *payload* that is a dict of 3 keys: *class*, *message*, *name*.
All these keys are mapped to string values.

.. code-block:: python
    :linenos:

    @dispatcher.rpc_error_method(service="remote_service", method="remote_method")
    def world_error(self, error, proxy):
        pass

Subscription handler
++++++++++++++++++++

:class:`tavrida.messages.IncomingNotification` routing is based on the name of remote publisher entry point.
Such entry point can be considered as notification topic.
For example for *test_hello* service and remote entry point *remote_service.remote_method* the correct entry point value is *remote_service.remote_method*

.. code-block:: python
    :linenos:

    @dispatcher.subscription_method(service="remote_service", method="remote_method")
    def hello_subscription(self, notification, proxy, param):
        pass

Resulting code example
++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from tavrida import dispatcher
    from tavrida import service

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

        @dispatcher.rpc_method(service="test_hello", method="hello")
        def handler(self, request, proxy, param):
            return {"parameter": "value"}

        @dispatcher.rpc_response_method(service="remote_service", method="remote_method")
        def world_resp(self, response, proxy, param):
            pass

        @dispatcher.rpc_error_method(service="remote_service", method="remote_method")
        def world_error(self, error, proxy):
            pass

        @dispatcher.subscription_method(service="remote_service", method="remote_method")
        def hello_subscription(self, notification, proxy, param):
            pass
