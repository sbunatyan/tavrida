Discovery
=========

Discovery object is used to discover remote service exchange to send messages to.

Discovery types
---------------

It holds 3 types of pairs *service_name:service_exchange*:

1. For remote service. Is used to send requests, responses, errors to remote service.
2. For remote service publisher. Is used to subscribe for notifications from remote service.
3. For local service publisher. Is used to publish notifications by local service.

Discovery service (.ds) config file
+++++++++++++++++++++++++++++++++++

To use .ds file you need to describe services in .ds file in format

.. code-block:: aconf

    [service1]
    exchange=service1_exchange
    notifications=service1_notifications

    [service2]
    exchange=service2_exchange
    notifications=service2_notifications

    [service3]
    exchange=service3_exchange
    notifications=service3_notifications

    [service4]
    exchange=service4_exchange

And then to load .ds file to :class:`tavrida.discovery.FileBasedDiscoveryService`

.. code-block:: python
    :linenos:

    from tavrida import discovery

    srv1_disc = discovery.FileBasedDiscoveryService("services.ds", "service1")

Discovery without .ds file
++++++++++++++++++++++++++

To register all types of services use :class:`tavrida.discovery.LocalDiscovery`:

.. code-block:: python
    :linenos:

    from tavrida import discovery

    disc = discovery.LocalDiscovery()

    # register remote service's exchange to send equests,
    # responses, errors
    disc.register_remote_service("remote_service", "remote_service_exchange")

    # register service notification exchange to publish notifications
    # Service 'local_service' publishes notifications to its exchange
    # 'local_service_exchange'
    disc.register_local_publisher("local_service", "local_service_exchange")

    # register remote notification exchange to bind to and get notifications
    # In this example service 'local_service' gets notifications to it's queue
    # from 'remote_notifications_exchange' which is the publication exchange of
    # service 'remote_Service'
    disc.register_remote_publisher("remote_service", "remote_notifications_exchange")

Discovery binding
-----------------

Before server starts each service that needs to interact with other service should be binded to one discovery object.

Therefore if you have multiple services and subsequently multiple discovery objects you should register each required remote or local service in corresponding discovery service.

.. code-block:: python
    :linenos:

    from tavrida import discovery

    disc = discovery.LocalDiscovery()
    disc.register_remote_service("remote_service", "remote_service_exchange")
    MyServiceController.set_discovery(disc)


Discovery for proxy
-------------------

Besides that you should provide discovery object while creation :class:`tavrida.client.RPCClient` object.

.. code-block:: python
    :linenos:

    from tavrida import client
    from tavrida import discovery

    disc = discovery.LocalDiscovery()
    disc.register_remote_service(service_name="remote_service",
                                 exchange_name="remote_exchange")
    cli = client.RPCClient(config=conf, service="test_hello", discovery=disc,
                           source=source)

Soon the discovery that uses central settings storage will be implemented.
But you can implement your own discovery class. The only demand is to inherit it from :class:`tavrida.discovery.AbstractDiscovery`
