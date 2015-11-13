import logging

import controller
import exceptions
import messages


class ValidateMessageMiddleware(controller.AbstractController):

    REQUIRED_HEADERS = ["message_id", "request_id", "message_type",
                        "source", "destination"]
    MESSAGE_TYPE = ["request", "response", "notification", "error"]

    def __init__(self):
        self.log = logging.getLogger(__name__)

    def _validate_headers(self, headers):
        for field in self.REQUIRED_HEADERS:
            if headers.get(field) is None:
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

    def process(self, ampq_message):
        self._validate_headers(ampq_message.headers)
        return ampq_message


class CreateMessageMiddleware(controller.AbstractController):

    def process(self, message_body):
        return messages.IncomingMessageFactory().create(message_body)


class CreateAMQPMiddleware(controller.AbstractController):

    def process(self, message):
        return messages.AMQPMessage.create_from_message(message)
