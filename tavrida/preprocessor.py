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
import steps


class PreProcessor(controller.AbstractController):

    """
    Preprocesses incoming messages. This class is responsible for message
    transfer to processor
    """

    def __init__(self, router, service_list):
        super(PreProcessor, self).__init__()
        self.log = logging.getLogger(__name__)
        self._router = router
        self._service_list = service_list
        self._steps = [
            steps.ValidateMessageMiddleware(),
            steps.CreateMessageMiddleware(),
            steps.LogIncomingAMQPMessageMiddleware()
        ]

    def process(self, amqp_message):
        """
        PreProcesses incoming message

        :param amqp_message: AMPQ message
        :type amqp_message: messages.AMQPMEssage
        :return: response object ot None
        :rtype: Response, Error or None
        """
        msg = amqp_message
        all_controllers = self._steps
        for step in all_controllers:
            msg = step.process(msg)
        self._router.process(msg, self._service_list)
