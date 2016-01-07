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
