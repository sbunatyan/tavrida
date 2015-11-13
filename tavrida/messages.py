import anyjson
import uuid

import entry_point


class AMQPMessage(object):

    """
    Container for raw AMQP message
    Stored raw body as string and headers as dict
    This class is used in AMQP drivers to send AMQP Message to preprocessor
    """

    def __init__(self, body, headers):
        super(AMQPMessage, self).__init__()
        self.body = body
        self.headers = headers

    @classmethod
    def create_from_message(cls, message):
        """
        Create AMQP message from Message. Method is used in postprocessor

        :param message: Message (Response, Error, Notifications, etc)
        :type message: message.Message
        :return: AMQPMessage object
        :type: AMQPMessage
        """
        return cls(message.body_serialize(), message.headers)

    def body_deserialize(self):
        """
        Deserializes raw JSON message to dict

        :return: deserialized body
        :type: dict
        """
        return anyjson.deserialize(self.body)


class Incoming(object):
    pass


class Outgoing(object):
    pass


class Message(object):

    """
    Base message class. Parent class for all messages
    """

    def __init__(self,
                 request_id,
                 message_type,
                 reply_to,
                 source,
                 destination,
                 context,
                 payload):

        super(Message, self).__init__()
        if not isinstance(source, entry_point.EntryPoint):
            raise TypeError('source must be EntryPoint')

        if not isinstance(payload, dict):
            raise TypeError('payload must be dict, received {}'
                            .format(type(payload)))

        self.request_id = request_id
        self.message_id = uuid.uuid4().hex
        self.message_type = message_type
        self.reply_to = reply_to
        self.source = source
        self.destination = destination
        self._context = context or {}
        self._payload = payload

    @property
    def headers(self):
        return {
            "request_id": self.request_id,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "reply_to": str(self.reply_to),
            "source": str(self.source),
            "destination": str(self.destination)
        }

    @property
    def context(self):
        return self._context

    @property
    def payload(self):
        return self._payload

    @property
    def type(self):
        return self.message_type

    def update_context(self, context):
        self._context.update(context)

    def body_serialize(self):
        """
        Serializes message to JSON

        :return: JSON representation
        :rtype: string
        """
        return anyjson.serialize({"payload": self.payload,
                                  "context": self.context})


class IncomingRequest(Message, Incoming):

    """
    Incoming request object
    """

    def __init__(self,
                 request_id,
                 reply_to,
                 source,
                 destination,
                 context,
                 **payload):
        super(IncomingRequest, self).__init__(
            request_id,
            "request",
            reply_to,
            source,
            destination,
            context,
            payload)


class IncomingRequestCall(IncomingRequest):

    """
    Incoming call request object
    """

    def make_response(self, **payload):
        """
        Create response to request

        :param payload: params and values
        :type payload: dict
        :return: response object
        :rtype: messages.Response
        """
        return Response.create_by_request(self, **payload)


class IncomingRequestCast(IncomingRequest):

    """
    Incoming cast request object
    """

    def __init__(self,
                 request_id,
                 source,
                 destination,
                 context,
                 **payload):
        super(IncomingRequestCast, self).__init__(
            request_id,
            entry_point.NullEntryPoint(),
            source,
            destination,
            context,
            **payload)


class Request(Message, Outgoing):

    """
    Outgoing request object
    """

    def __init__(self,
                 reply_to,
                 source,
                 destination,
                 context,
                 **payload):
        request_id = uuid.uuid4().hex
        super(Request, self).__init__(
            request_id,
            "request",
            reply_to,
            source,
            destination,
            context,
            payload)

    @classmethod
    def create_transfer(cls, request_id, reply_to, source, destination,
                        **payload):

        req = cls(reply_to, source, destination, **payload)
        req.request_id = request_id
        return req


class BaseResponse(Message):

    """
    Base response object
    """

    def __init__(self,
                 request_id,
                 source,
                 destination,
                 context,
                 **payload):

        super(BaseResponse, self).__init__(
            request_id,
            "response",
            entry_point.NullEntryPoint(),
            source,
            destination,
            context,
            payload)


class IncomingResponse(BaseResponse, Incoming):

    """
    Incoming response object
    """
    pass


class Response(BaseResponse, Outgoing):

    """
    Outgoing response object
    """

    @classmethod
    def create_by_request(cls, request, **payload):

        """
        Create response to request

        :param request: request
        :type request: messages.IncomingRequest
        :param payload: params and values
        :type payload: dict
        :return: response object
        :rtype: messages.Response
        """

        return cls(
            request_id=request.request_id,
            source=request.destination,
            destination=request.reply_to,
            context=request.context,
            **payload
        )


class BaseError(Message):

    """
    Base error message
    """

    def __init__(self,
                 request_id,
                 source,
                 destination,
                 context,
                 **payload):

        super(BaseError, self).__init__(
            request_id,
            "error",
            entry_point.NullEntryPoint(),
            source,
            destination,
            context,
            payload)


class IncomingError(BaseError, Incoming):

    """
    Incoming error message
    """
    pass


class Error(BaseError, Outgoing):

    """
    Outgoing error message
    """

    def __init__(self,
                 request_id,
                 source,
                 destination,
                 context,
                 exception):

        try:
            code = exception.code
        except AttributeError:
            code = None

        payload = {
            "class": exception.__class__.__name__,
            "message": str(exception),
            "code": code
        }
        super(Error, self).__init__(
            request_id,
            source,
            destination,
            context,
            **payload)

    @classmethod
    def create_by_request(cls, request, exception):
        """
        Create error to request

        :param request: request
        :type request: messages.IncomingRequest
        :param exception: exception to send
        :type exception: Exception
        :return: response object
        :rtype: messages.Response
        """

        return cls(
            request_id=request.request_id,
            source=request.destination,
            destination=request.reply_to,
            context=request.context,
            exception=exception
        )


class IncomingNotification(Message, Incoming):

    """
    Incoming notification message
    """

    def __init__(self,
                 request_id,
                 source,
                 context,
                 **payload):
        super(IncomingNotification, self).__init__(
            request_id,
            "notification",
            entry_point.NullEntryPoint(),
            source,
            entry_point.NullEntryPoint(),
            context,
            payload)


class Notification(Message, Outgoing):

    """
    Outgoing notification message
    """

    def __init__(self,
                 source,
                 context,
                 **payload):
        request_id = uuid.uuid4().hex
        super(Notification, self).__init__(
            request_id,
            "notification",
            entry_point.NullEntryPoint(),
            source,
            entry_point.NullEntryPoint(),
            context,
            payload)


class IncomingMessageFactory(object):

    """
    Factory creates incoming messages by AMQP message
    """

    def _get_request_cls(self, reply_to):

        """
        Returns corresponding request class

        :param reply_to: entry point to reply
        :type reply_to: entry_point.EntryPoint
        :return: IncomingRequestCall or IncomingRequestCast
        :rtype: messages.IncomingRequest
        """

        if not isinstance(reply_to, entry_point.NullEntryPoint):
            return IncomingRequestCall
        else:
            return IncomingRequestCast

    def _get_response_cls(self):
        """
        Returns Incoming response class

        :return: Incoming response
        :trype: IncomingResponse
        """
        return IncomingResponse

    def _get_error_cls(self):
        """
        Returns Incoming error class

        :return: Incoming error
        :rtype: IncomingError
        """
        return IncomingError

    def _get_notification_cls(self):
        """
        Returns Incoming notification class

        :return: Incoming notification
        :rtype: IncomingNotification
        """
        return IncomingNotification

    def get_class(self, message_type, reply_to):
        """
        Return correct message class

        :param message_type: Message type
        :type message_type: string
        :param reply_to: entry point to reply
        :type reply_to: entry_point.EntryPoint
        :return: class of matching message type
        :rtype: Message
        """
        if message_type == "request":
            return self._get_request_cls(reply_to)
        elif message_type == "response":
            return self._get_response_cls()
        elif message_type == "notification":
            return self._get_notification_cls()
        elif message_type == "error":
            return self._get_error_cls()

    def _create_request_call(self, payload, context, request_id, source,
                             destination, reply_to):
        """
        Creates incoming request call object

        :param payload: message payload
        :type payload: dict
        :param request_id: request ID
        :type request_id: string
        :param source: message source
        :type source: entry_point.Source
        :param destination: message destination
        :type destination: entry_point.Destination
        :param reply_to: message entry point to reply to
        :type reply_to: entry_point.EntryPoint
        :return: incoming request object
        :rtype: IncomingRequestCall
        """
        return IncomingRequestCall(request_id,
                                   reply_to,
                                   source,
                                   destination,
                                   context,
                                   **payload)

    def _create_message(self, message_cls, payload, context, request_id,
                        source, destination):
        """
        Creates incoming response call object

        :param message_cls: message class
        :type message_cls: messages.Message
        :param payload: message payload
        :type payload: dict
        :param request_id: request ID
        :type request_id: string
        :param source: message source
        :type source: entry_point.Source
        :param destination: message destination
        :type destination: entry_point.Destination
        :return: message_cls
        :rtype: messages.Message
        """

        return message_cls(request_id,
                           source,
                           destination,
                           context,
                           **payload)

    def _create_error(self, payload, context, request_id, source, destination):
        """
        Creates incoming error call object

        :param payload: message payload
        :type payload: dict
        :param request_id: request ID
        :type request_id: string
        :param source: message source
        :type source: entry_point.Source
        :param destination: message destination
        :type destination: entry_point.Destination
        :return: incoming error object
        :rtype: IncomingError
        """

        err = IncomingError(request_id, source, destination, context,
                            **payload)
        return err

    def create_nofification(self, payload, context, request_id, source):
        """
        Creates incoming notification call object

        :param payload: message payload
        :type payload: dict
        :param request_id: request ID
        :type request_id: string
        :param source: message source
        :type source: entry_point.Source
        :return: incoming notification object
        :rtype: IncomingNotification
        """
        return IncomingNotification(request_id, source, context, **payload)

    def create(self, amqp_message):
        """
        Create corresponding message object by AMQP message

        :param amqp_message: AMQP message
        :type amqp_message: messages.AMQPMessage
        :return: message object
        :rtype: messages.Message
        """

        headers = amqp_message.headers
        destination = entry_point.EntryPointFactory().create(
            headers["destination"], destination=True)
        reply_to = entry_point.EntryPointFactory().create(
            headers["reply_to"])
        source = entry_point.EntryPointFactory().create(headers["source"],
                                                        source=True)

        message_cls = self.get_class(headers["message_type"], reply_to)
        body = amqp_message.body_deserialize()
        payload = body["payload"]
        context = body["context"]
        if issubclass(message_cls, IncomingRequestCall):
            return self._create_request_call(payload, context,
                                             headers["request_id"],
                                             source, destination, reply_to)
        elif issubclass(message_cls, Error):
            return self._create_error(payload, context,
                                      headers["request_id"], source,
                                      destination)
        elif issubclass(message_cls, IncomingNotification):
            return self.create_nofification(payload, context,
                                            headers["request_id"], source)
        else:
            return self._create_message(message_cls,
                                        payload, context,
                                        headers["request_id"],
                                        source, destination)
