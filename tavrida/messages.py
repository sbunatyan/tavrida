#!/usr/bin/env python
# Copyright (c) 2015 Sergey Bunatyan <sergey.bunatyan@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import anyjson
import copy
import logging
import uuid

import entry_point
import exceptions
import utils


class AMQPMessage(object):

    """
    Container for raw AMQP message
    Stored raw body as string and headers as dict
    This class is used in AMQP drivers to send AMQP Message to preprocessor
    """

    REQUIRED_HEADERS = ["correlation_id", "message_id", "request_id",
                        "message_type", "source", "destination"]
    MESSAGE_TYPE = ["request", "response", "notification", "error"]

    def __init__(self, body, headers):
        super(AMQPMessage, self).__init__()
        self.body = body
        self.headers = headers
        self.log = logging.getLogger(__name__)

    def _validate_headers(self, headers):
        for field in self.REQUIRED_HEADERS:
            if field not in headers:
                raise exceptions.FieldMustExist(field=field)
        self._validate_message_type(headers["message_type"])
        self._validate_message_type(headers["message_type"])
        self._validate_entry_point(headers["source"], "source")
        if headers["reply_to"]:
            self._validate_entry_point(headers["reply_to"], "reply_to")
        if headers["destination"]:
            self._validate_entry_point(headers["destination"], "destination")

    def _validate_message_type(self, message_type):
        if message_type not in self.MESSAGE_TYPE:
            raise exceptions.UnsuitableFieldValue(field="message_type",
                                                  value=message_type)

    def _validate_entry_point(self, value, name):
        if not value:
            raise exceptions.FieldMustFullyDefined(field=name)

    def validate(self):
        self._validate_headers(self.headers)

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
                 headers,
                 context,
                 payload):

        super(Message, self).__init__()

        if not headers.get("message_id"):
            headers["message_id"] = uuid.uuid4().hex

        self.correlation_id = headers.get("correlation_id")
        self.request_id = headers.get("request_id")
        self.message_id = headers.get("message_id")
        self.message_type = headers.get("message_type")
        self.reply_to = entry_point.EntryPointFactory().create(
            headers.get("reply_to"))
        self.source = entry_point.EntryPointFactory().create(
            headers.get("source"), source=True)
        self.destination = entry_point.EntryPointFactory().create(
            headers.get("destination"), destination=True)

        self._headers = copy.copy(headers)
        self._context = context or {}
        self._payload = payload

        if not isinstance(self.source, entry_point.EntryPoint):
            raise TypeError('source must be EntryPoint')

        if not isinstance(payload, dict):
            raise TypeError('payload must be dict, received {}'
                            .format(type(payload)))

    @property
    def headers(self):
        return self._headers

    @property
    def context(self):
        return self._context

    @property
    def payload(self):
        return self._payload

    @property
    def body(self):
        return self.payload

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
        return Response.create_by_request(self, payload)


class IncomingRequestCast(IncomingRequest):

    """
    Incoming cast request object
    """


class Request(Message, Outgoing):

    """
    Outgoing request object
    """

    def __init__(self, headers, context, payload):
        headers = copy.copy(headers)
        if not headers["correlation_id"]:
            headers["correlation_id"] = str(uuid.uuid4())
        headers["request_id"] = uuid.uuid4().hex
        headers["message_type"] = "request"
        super(Request, self).__init__(headers, context, payload)

    @classmethod
    def create_transfer(cls, headers, context, **payload):
        req = cls(headers, context, payload)
        return req


class BaseResponse(Message):

    """
    Base response object
    """

    def __init__(self, headers, context, payload):
        headers = copy.copy(headers)
        headers["reply_to"] = str(entry_point.NullEntryPoint())
        headers["message_type"] = "response"
        super(BaseResponse, self).__init__(headers, context, payload)


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
    def create_by_request(cls, request, payload):

        """
        Create response to request

        :param request: request
        :type request: messages.IncomingRequest
        :param payload: params and values
        :type payload: dict
        :return: response object
        :rtype: messages.Response
        """
        headers = {
            "correlation_id": request.correlation_id,
            "request_id": request.request_id,
            "source": str(request.destination),
            "destination": str(request.reply_to or request.source),
            "reply_to": ""
        }
        request_headers = request.headers.copy()
        request_headers.update(headers)
        return cls(request_headers, request.context, payload)


class BaseError(Message):

    """
    Base error message
    """

    def __init__(self, headers, context, payload):
        headers = copy.copy(headers)
        headers["reply_to"] = str(entry_point.NullEntryPoint())
        headers["message_type"] = "error"
        super(BaseError, self).__init__(headers, context, payload)


class IncomingError(BaseError, Incoming):

    """
    Incoming error message
    """
    pass


class Error(BaseError, Outgoing):

    """
    Outgoing error message
    """

    def __init__(self, headers, context, exception):

        try:
            code = exception.code
        except AttributeError:
            code = exceptions.UNKNOWN_ERROR

        payload = {
            "class": utils.get_fqcn(exception),
            "message": str(exception),
            "code": code
        }
        super(Error, self).__init__(headers, context, payload)

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
        headers = {
            "correlation_id": request.correlation_id,
            "request_id": request.request_id,
            "source": str(request.destination),
            "destination": str(request.reply_to or request.source),
            "reply_to": ""
        }
        request_headers = request.headers.copy()
        request_headers.update(headers)
        return cls(request_headers, request.context, exception)


class IncomingNotification(Message, Incoming):

    """
    Incoming notification message
    """

    def __init__(self, headers, context, payload):
        headers = copy.copy(headers)
        headers["reply_to"] = str(entry_point.NullEntryPoint())
        headers["destination"] = str(entry_point.NullEntryPoint())
        headers["message_type"] = "notification"
        super(IncomingNotification, self).__init__(headers, context, payload)


class Notification(Message, Outgoing):

    """
    Outgoing notification message
    """

    def __init__(self, headers, context, payload):
        headers = copy.copy(headers)
        headers["reply_to"] = str(entry_point.NullEntryPoint())
        headers["destination"] = str(entry_point.NullEntryPoint())
        headers["message_type"] = "notification"
        headers["request_id"] = uuid.uuid4().hex

        if not headers["correlation_id"]:
            headers["correlation_id"] = str(uuid.uuid4())

        super(Notification, self).__init__(headers, context, payload)


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

    def _create_request_call(self, headers, context, payload):
        """
        Creates incoming request call object

        :param headers: headers
        :type headers: dict
        :param context: headers
        :type context: dict
        :param payload: message payload
        :type payload: dict
        :return: incoming request object
        :rtype: IncomingRequestCall
        """
        return IncomingRequestCall(headers, context, payload)

    def _create_message(self, message_cls, headers, context, payload):
        """
        Creates incoming response call object

        :param headers: headers
        :type headers: dict
        :param context: headers
        :type context: dict
        :param payload: message payload
        :type payload: dict
        :return: message_cls
        :rtype: messages.Message
        """

        return message_cls(headers, context, payload)

    def _create_error(self, headers, context, payload):
        """
        Creates incoming error call object

        :param headers: headers
        :type headers: dict
        :param context: headers
        :type context: dict
        :param payload: message payload
        :type payload: dict
        :return: incoming error object
        :rtype: IncomingError
        """

        err = IncomingError(headers, context, payload)
        return err

    def create_notification(self, headers, context, payload):
        """
        Creates incoming notification call object

        :param headers: headers
        :type headers: dict
        :param context: headers
        :type context: dict
        :param payload: message payload
        :type payload: dict
        :return: incoming notification object
        :rtype: IncomingNotification
        """
        return IncomingNotification(headers, context, payload)

    def create(self, amqp_message):
        """
        Create corresponding message object by AMQP message

        :param amqp_message: AMQP message
        :type amqp_message: messages.AMQPMessage
        :return: message object
        :rtype: messages.Message
        """

        headers = amqp_message.headers
        reply_to = entry_point.EntryPointFactory().create(
            headers["reply_to"])

        message_cls = self.get_class(headers["message_type"], reply_to)
        body = amqp_message.body_deserialize()
        payload = body["payload"]
        context = body["context"]
        if issubclass(message_cls, IncomingRequestCall):
            return self._create_request_call(headers, context, payload)
        elif issubclass(message_cls, Error):
            return self._create_error(headers, context, payload)
        elif issubclass(message_cls, IncomingNotification):
            return self.create_notification(headers, context, payload)
        else:
            return self._create_message(message_cls, headers, context, payload)
