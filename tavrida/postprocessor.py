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
import entry_point
import steps


class PostProcessor(controller.AbstractController):

    """
    Processes outgoing messages. This class is responsible for message
    transfer to writer
    """

    def __init__(self, driver, discovery):
        super(PostProcessor, self).__init__()
        self.log = logging.getLogger(__name__)
        self._driver = driver
        self._discovery = discovery
        self._steps = [
            steps.CreateAMQPMiddleware(),
            steps.ValidateMessageMiddleware(),
            steps.LogOutgoingAMQPMessageMiddleware(),
        ]

    def process(self, message_obj):
        """
        Processes outgoing message

        :param message_obj: message
        :type message_obj: messages.Message
        """
        msg = message_obj
        all_controllers = self._steps
        for step in all_controllers:
            msg = step.process(msg)
        self._send(msg)

    @property
    def discovery_service(self):
        return self._discovery

    @property
    def driver(self):
        return self._driver

    def set_discovery(self, discovery):
        self._discovery = discovery

    def _send(self, message):
        """
        Sends AMQP message to exchange via writer

        :param message: AMQP message to send
        :type message: messages.AMQPMessage
        :return:
        """
        discovery_service = self.discovery_service
        if message.headers["message_type"] == "notification":
            source = message.headers["source"]
            ep = entry_point.EntryPointFactory().create(source)
            exchange = discovery_service.get_local_publisher(ep.service)
        elif message.headers["message_type"] in ("response", "error"):
            rk = message.headers["destination"]
            ep = entry_point.EntryPointFactory().create(rk)
            exchange = discovery_service.get_remote(ep.service)
        else:
            dst = message.headers["destination"]
            ep = entry_point.EntryPointFactory().create(dst)
            exchange = discovery_service.get_remote(ep.service)
        routing_key = ep.to_routing_key()
        self._driver.publish_message(exchange, routing_key, message)
