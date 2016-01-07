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


class Middleware(controller.AbstractMessageController):

    """
    Base middleware class. Any middleware should be inherited from this class.
    Middlewares could be added for processing message before and after the
    handler call.
    """

    def process(self, message):
        """
        Processes message.
        This method should be redefined.

        :param message: incoming/outgoing message
        :type message: messages.Message
        :return: modified or new message
        :rtype: message.Message
        """
        return message
