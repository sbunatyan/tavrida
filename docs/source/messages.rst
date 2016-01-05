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
:class:`tavrida.messages.Notification` and there structure is the same as fro incoming messages.