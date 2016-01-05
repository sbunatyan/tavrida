Tavrida Tutorial
================

Request Handling
----------------

Simple service that handles request
+++++++++++++++++++++++++++++++++++

To implement simple service just follow the next steps:

1. Declare service controller
2. Define handler for some entry point (test_hello.hello)
3. Implement custom handler logic
4. Create configuration to connect to RabbitMQ
5. Create server that listens queue and publishes messages for given services
6. Start the server

Service Hello
+++++++++++++

.. code-block:: python
    :linenos:

    from tavrida import config
    from tavrida import dispatcher
    from tavrida import server
    from tavrida import service

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

        @dispatcher.rpc_method(service="test_hello", method="hello")
        def handler(self, request, proxy, param):
            print param

    def run():

        creds = config.Credentials("guest", "guest")
        conf = config.ConnectionConfig("localhost", credentials=creds,
                                       async_engine=True)
        srv = server.Server(conf,
                            queue_name="test_service",
                            exchange_name="test_exchange",
                            service_list=[HelloController])
        srv.run()

To implement a client that makes calls to service use the following steps:

1. Create configuration to connect to RabbitMQ
2. Create discovery object. Discovery object is used to discover remote service's exchange by service name.
3. Create a client for a particular service. The source value is required and is useful for troubleshooting.
4. Make call to remote service. *Cast* function call is usual for client that lives outside RPC service. *Cast* means that you don't expect a response. As you make your call from some script, not from a service, you don't expect response.

Client to call Hello service
++++++++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from tavrida import client
    from tavrida import config
    from tavrida import discovery
    from tavrida import entry_point

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds)

    disc = discovery.LocalDiscovery()
    disc.register_remote_service(service_name="test_hello",
                                 exchange_name="test_exchange")
    cli = client.RPCClient(config=conf, service="test_hello", discovery=disc,
                           source="client_app")
    cli.hello(param=123).cast()


Two services that intercommunicate (Request, Response, Error handling)
----------------------------------------------------------------------

In this example we omit the client script as it's absolutely the same as in the previous example.
Let's implement service *Hello* that handles request from some outer client, makes requests to the *World* service and handles responses and error messages from it.

1. Declare Hello service controller
2. Define handler for some entry point (test_hello.hello)
3. In this handler implement a call to the *World* service via proxy object. Give attention to that we use *call* method as we expect the response from *World* service.
4. Define handlers for response and error from remote entry point (test_world.world). Error handler always takes **only 2 parameters**: error message object and proxy object.
5. Create discovery object and register remote service (test_world). Discovery object is used to discover remote service's exchange by service name.
6. Bind discovery object to service controller.
7. Create configuration to connect to RabbitMQ
8. Create server that listens queue and publishes messages for given services
9. Start the server

Service Hello
+++++++++++++

.. code-block:: python
    :linenos:

    from tavrida import config
    from tavrida import dispatcher
    from tavrida import server
    from tavrida import service

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

        @dispatcher.rpc_method(service="test_hello", method="hello")
        def handler(self, request, proxy, param):
            print "---- request to hello ----"
            print param
            proxy.test_world.world(param=12345).call()

        @dispatcher.rpc_response_method(service="test_world", method="world")
        def world_resp(self, response, proxy, param):
            # Handles responses from test_world.world
            print "---- response from world to hello ----"
            print response.context
            print response.headers
            print param # == "world response"
            print "--------------------------------------"

        @dispatcher.rpc_error_method(service="test_world", method="world")
        def world_error(self, error, proxy):
            # Handles error from test_world.world
            print "---- error from hello ------"
            print error.context
            print error.headers
            print error.payload
            print "----------------------------"

    def run():

        disc = discovery.LocalDiscovery()

        # register remote service's exchanges to send there requests (RPC calls)
        disc.register_remote_service("test_world", "test_world_exchange")
        HelloController.set_discovery(disc)

        # define connection parameters
        creds = config.Credentials("guest", "guest")
        conf = config.ConnectionConfig("localhost", credentials=creds,
                                       async_engine=True)
        # create server
        srv = server.Server(conf,
                            queue_name="test_service",
                            exchange_name="test_exchange",
                            service_list=[HelloController])
        srv.run()

Service World
+++++++++++++

Steps to implement the world service are pretty similar to the previous example.
The only difference is remote service registration (test_hello) and binding the discovery object to service controller.
In this example remote service registration is needed to send responses and error messages to test_hello service.

.. code-block:: python
    :linenos:

    from tavrida import config
    from tavrida import dispatcher
    from tavrida import server
    from tavrida import service

    @dispatcher.rpc_service("test_world")
    class WorldController(service.ServiceController):

        @dispatcher.rpc_method(service="test_world", method="world")
        def world(self, request, proxy, param):
            print "---- request to world------"
            print request.context
            print request.headers
            print param # == 12345
            print "---------------------------"
            return {"param": "world response"}

    def run():

        disc = discovery.LocalDiscovery()

        # register remote service's exchange to send there requests,
        # responses, errors
        disc.register_remote_service("test_hello", "test_exchange")
        WorldController.set_discovery(disc)

        creds = config.Credentials("guest", "guest")
        conf = config.ConnectionConfig("localhost", credentials=creds)

        srv = server.Server(conf,
                            queue_name="test_world_service",
                            exchange_name="test_world_exchange",
                            service_list=[WorldController])
        srv.run()


Publication and Subscription
----------------------------

1. Declare Hello service controller
2. In any request handler (or single script) use proxy to publish notification

Hello Service (publisher)
+++++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from tavrida import config
    from tavrida import dispatcher
    from tavrida import server
    from tavrida import service

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

        @dispatcher.rpc_method(service="test_hello", method="hello")
        def handler(self, request, proxy, param):
            print param
            proxy.publish(param="hello publication")

    def run():

        # register service's notification exchange to publish notifications
        # Service 'test_hello' publishes notifications to it's exchange
        # 'test_notification_exchange'
        disc = discovery.LocalDiscovery()
        disc.register_local_publisher("test_hello",
                                      "test_notification_exchange")
        HelloController.set_discovery(disc)

        creds = config.Credentials("guest", "guest")
        conf = config.ConnectionConfig("localhost", credentials=creds,
                                       async_engine=True)
        srv = server.Server(conf,
                            queue_name="test_service",
                            exchange_name="test_exchange",
                            service_list=[HelloController])
        srv.run()

1. Declare World service controller
2. Define subscription method

World service (subscriber)
++++++++++++++++++++++++++

.. code-block:: python
    :linenos:

    from tavrida import config
    from tavrida import dispatcher
    from tavrida import server
    from tavrida import service

    @dispatcher.rpc_service("test_world")
    class WorldController(service.ServiceController):

        @dispatcher.subscription_method(service="test_hello", method="hello")
        def hello_subscription(self, notification, proxy, param):
            print "---- notification from hello ------"
            print param # == "hello publication"

    def run():

        # register remote notification exchange to bind and get notifications
        # In this example service 'test_subscribe' gets notifications to it's queue
        # from 'test_notification_exchange' which is the publication exchange of
        # service 'test_hello'
        disc = discovery.LocalDiscovery()
        disc.register_remote_publisher("test_hello",
                                       "test_notification_exchange")
        WorldController.set_discovery(disc)

        creds = config.Credentials("guest", "guest")
        conf = config.ConnectionConfig("localhost", credentials=creds)

        srv = server.Server(conf,
                            queue_name="test_world_service",
                            exchange_name="test_world_exchange",
                            service_list=[WorldController])
        srv.run()
