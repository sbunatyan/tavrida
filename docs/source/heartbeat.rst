Heartbeat
=========

In case you have long-running handlers you may need to send heartbeats to
RabbitMQ.

Restriction
-----------

There is a `Pika <https://pika.readthedocs.org/en/0.10.0/index.html>`_.
restriction: heartbeats are available *only for sync engine*
(Blocking connection)

To send heartbeat from you controller use the method
:func:`tavrida.service.ServiceController.send_heartbeat`:

.. code-block:: python
    :linenos:

    from tavrida import service

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

    @dispatcher.rpc_method(service="test_hello", method="hello")
    def hello1(self, request, proxy, param):
        # part of long running logic
        self.send_heartbeat()
        # part of long running logic
