Client
======

To execute calls from third-party applications use :class:`tavrida.client.RPCClient` object.

Client parameters
-----------------

* You can pass optional *correlation_id* parameter. If remote service executes the subsequent call to the next service *correlation_id* will passed.

* You can pass additional *header* parameters to the remote service.

There are several ways to create and use client.


.. code-block:: python
    :linenos:

    from tavrida import client
    from tavrida import config
    from tavrida import discovery
    from tavrida import entry_point

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds)

    # You should provide discovery service object to client
    disc = discovery.LocalDiscovery()
    disc.register_remote_service(service_name="test_hello",
                                 exchange_name="test_exchange")

    cli = client.RPCClient(config=conf, discovery=disc, source=source)
    cli.test_hello.hello(param=123).cast(correlation_id="123-456")


.. code-block:: python
    :linenos:

    from tavrida import client
    from tavrida import config
    from tavrida import discovery
    from tavrida import entry_point

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds)

    # You should provide discovery service object to client
    disc = discovery.LocalDiscovery()
    disc.register_remote_service(service_name="test_hello",
                                 exchange_name="test_exchange")

    # If you want to provide source as a string
    cli = client.RPCClient(config=conf, discovery=disc, source="source_service")
    cli.test_hello.hello(param=123).cast(correlation_id="123-456")

    cli = client.RPCClient(config=conf, discovery=disc, source="source.method")
    cli.test_hello.hello(param=123).cast(correlation_id="123-456")
