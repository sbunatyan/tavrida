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
import logging

import controller
import messages


class ValidateMessageMiddleware(controller.AbstractController):
    """
    Validates message headers
    """

    def process(self, ampq_message):
        ampq_message.validate()
        return ampq_message


class CreateMessageMiddleware(controller.AbstractController):
    """
    Creates message from raw RabbitMQ message
    """

    def process(self, message_body):
        return messages.IncomingMessageFactory().create(message_body)


class CreateAMQPMiddleware(controller.AbstractController):
    """
    Creates intermediate AMQP message
    """

    def process(self, message):
        return messages.AMQPMessage.create_from_message(message)


class LoggingMiddleware(controller.AbstractController):
    """Controller contains method to hide sensitive headers."""

    SENSITIVE_HEADERS = ('authorization', 'proxy-authorization')

    def __init__(self):
        super(LoggingMiddleware, self).__init__()
        self._log = logging.getLogger(__name__)

    def _hide_sensitive_data(self, headers):
        processed_headers = headers.copy()
        old_keys = headers.keys()

        # Turn keys to lower case
        for k in old_keys:
            processed_headers[k.lower()] = processed_headers.pop(k)

        for sensitive in self.SENSITIVE_HEADERS:
            if sensitive in processed_headers:
                processed_headers[sensitive] = '<%s>' % sensitive

        # Turn keys to original case
        for k in old_keys:
            processed_headers[k] = processed_headers.pop(k.lower())
        return processed_headers


class LogIncomingAMQPMessageMiddleware(LoggingMiddleware):
    """Writes AMQP headers and body to log with level DEBUG.

    Hides values of SENSITIVE_HEADERS.

    Returns unmodified input message.
    """

    def process(self, message):
        if self._log.getEffectiveLevel() == logging.DEBUG:
            headers = self._hide_sensitive_data(message.headers)
            self._log.debug(
                "Incoming AMQP message with headers '%s' and body '%s'",
                headers, message.body)
        return message


class LogOutgoingAMQPMessageMiddleware(LoggingMiddleware):
    """Writes AMQP headers and body to log with level DEBUG.

    Hides values of SENSITIVE_HEADERS.

    Returns unmodified input message.
    """

    def process(self, message):
        if self._log.getEffectiveLevel() == logging.DEBUG:
            headers = self._hide_sensitive_data(message.headers)
            self._log.debug(
                "Outgoing AMQP message with headers '%s' and body '%s'",
                headers, message.body)
        return message
