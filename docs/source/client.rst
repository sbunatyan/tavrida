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

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds)

    cli = client.RPCClient(config=conf, service="remote_service",
                           exchange="remote_exchange",
                           source="source_application")
    cli.hello(param=123).cast(correlation_id="123-456")

.. code-block:: python
    :linenos:

    from tavrida import client
    from tavrida import config
    from tavrida import discovery

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds)

    disc = discovery.LocalDiscovery()
    disc.register_remote_service(service_name="remote_service",
                                 exchange_name="remote_exchange")

    cli = client.RPCClient(config=conf, service="remote_service",
                           source="source_application")
    cli.hello(param=123).cast(correlation_id="123-456")

.. code-block:: python
    :linenos:

    from tavrida import client
    from tavrida import config
    from tavrida import entry_point

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds)

    source = entry_point.Source("client", "method")
    cli = client.RPCClient(config=conf, service="remote_service",
                           exchange="remote_exchange", source=source,
                           headers={"aaa": "bbb"})
    cli.hello(param=123).cast()
