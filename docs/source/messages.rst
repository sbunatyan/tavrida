Messages
========

Messages that are used in handlers are of two types: Incoming and Outgoing

Incoming messages
-----------------

There 4 types of incoming messages:
:class:`tavrida.messages.IncomingRequest`,
:class:`tavrida.messages.IncomingResponse`,
:class:`tavrida.messages.IncomingError`,
:class:`tavrida.messages.IncomingNotification`

All messages have properties:

+----------------+------------------------------------------+--------------------------------------------+
|  Property      |                     Type                 | Description                                |
+================+==========================================+============================================+
| correlation_id |                   string                 | Unique identifier of remote service calls  |
|                |                                          | chain.                                     |
+----------------+------------------------------------------+--------------------------------------------+
| request_id     |                   string                 | Unique identifier of pair                  |
|                |                                          | request - response/error                   |
+----------------+------------------------------------------+--------------------------------------------+
| message_id     |                   string                 | Unique single message identifier           |
+----------------+------------------------------------------+--------------------------------------------+
| message_type   |                   string                 |   Message type: request, response, error,  |
|                |                                          |  notification                              |
+----------------+------------------------------------------+--------------------------------------------+
| reply_to       | :class:`tavrida.entry_point.EntryPoint`  |   Entry point to send response/error to    |
+----------------+------------------------------------------+--------------------------------------------+
| source         | :class:`tavrida.entry_point.EntryPoint`  |   Entry point of the message source        |
+----------------+------------------------------------------+--------------------------------------------+
| destination    | :class:`tavrida.entry_point.EntryPoint`  |   Entry point of the message destination   |
+----------------+------------------------------------------+--------------------------------------------+
| headers        |                   dict                   | dict of message headers (properties above) |
+----------------+------------------------------------------+--------------------------------------------+
| context        |                   dict                   | dict if context values                     |
+----------------+------------------------------------------+--------------------------------------------+
| payload        |                   dict                   | dict of incoming handler parameters        |
+----------------+------------------------------------------+--------------------------------------------+

Notes
+++++

**correlation_id** - Unique identifier of the chain of calls between multiple services. For example: A <-> B <-> C -> D.

**request_id** -  Unique identifier of the pair of messages request - response/error between 2 services. For example: A <-> B.

**headers** - dict of the properties above (named headers). It is mutable unlike properties. But headers and properties are not synchronized.

**context** - additional data that can be used in handlers. By default contains payload data and is updated at each hop. That means that if you have a chain if requests, context will be updated with all incoming parameters of each handler.
As it is a simple dict the conflicting keys will be overwritten.


Outgoing messages
-----------------

There 4 types of incoming messages:
:class:`tavrida.messages.Request`,
:class:`tavrida.messages.Response`,
:class:`tavrida.messages.Error`,
:class:`tavrida.messages.Notification` and their structure is the same as for incoming messages.

Under the hood
--------------

Messages are transported via RabbitMQ. Message headers are fair RabbitMQ headers:
correlation_id, request_id, message_id, message_type, reply_to, source, source, destination.

Message payload is a valid JSON object that consists of 2 sub-objects:

.. code-block:: python

    {
        "context": {"some_key": "some_value"},
        "payload": {"parameter": "value"}
    }

**context** holds arbitrary values. By default it is filled with the payload values and is updated after each request.
That means that if you have a chain of 2 calls: service A -> service B -> service C, context will hold incoming parameters for both calls.
But if at any hop parameter names are equal, the old value is overwritten by the new one.
Actually context is just a python dict that is updated with "update" method.


**payload** holds custom parameters that defined in handler. Names of payload keys should be equal to names of handler parameters.
If you have a handler:

.. code-block:: python

    @dispatcher.rpc_method(service="test_hello", method="hello")
    def handler(self, request, proxy, param1, param1):
        return {"param3": "value3"}

your payload should look like:

.. code-block:: python

     "payload": {"param1": "value1", "param2": "value2"}
