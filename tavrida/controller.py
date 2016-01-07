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

import abc


class AbstractController(object):

    """
    Abstract controller should be used to implement arbitrary controllers in
    the chain of actions on some object
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def process(self, *args, **kwargs):
        pass


class AbstractMessageController(AbstractController):

    """
    Abstract controller should be used to implement arbitrary controllers in
    the chain of actions on message
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def process(self, message):
        """

        :param message:  Message of arbitrary type
        :return: Any result, mainly message
        """
        pass
