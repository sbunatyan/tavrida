Configuration
=============

Config parameters
-----------------

Tavrida configuration passes most of the parameters to `pika <https://pika.readthedocs.org/en/0.10.0/index.html>`_.
Information about them you can find `here <https://pika.readthedocs.org/en/0.10.0/modules/parameters.html>`_.

The Tavrida specific configuration parameters are:

* *reconnect_attempts* (Int) - number of attempts to reconnect to RabbitMQ on failure. The negative value means **infinite** number. The **default** is **-1**.
* *async_engine* (Bool) - use pika SelectConnection. It is more productive but less tested. By **default** is **False**.

Example:

.. code-block:: python
    :linenos:

    from tavrida import config

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig(host="localhost",
                                   credentials=creds,
                                   port=5672,
                                   reconnect_attempts=3,
                                   async_engine=True)
