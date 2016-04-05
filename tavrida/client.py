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

import copy

from tavrida.amqp_driver import driver
from tavrida import discovery
from tavrida import entry_point
from tavrida import postprocessor
from tavrida import proxies


class RPCClient(object):

    """
    Client to make RPC calls to remove service.
    Calls are executed via service proxies.

    >>> from tavrida import config
    >>> credentials = config.Credentials("username", "password")
    >>> config = config.ConnectionConfig("localhost", credentials)
    >>> disc = discovery.LocalDiscovery()
    >>> disc.register_remote_service("service_name", "service_exchange")
    >>> headers = {"header": "value"}
    >>> cli = RPCClient(config, disc, source="some_client", headers=headers)
    >>> cli.some_method(some_parameter="1234").cast()
    """

    def __init__(self, config, discovery, source="", context=None,
                 headers=None):
        super(RPCClient, self).__init__()
        self._config = config
        self._discovery = discovery
        self._source = source
        self._headers = copy.copy(headers) or {}
        self._context = copy.copy(context) if context else None

    def _get_discovery(self):
        return discovery.LocalDiscovery()

    def _get_driver(self):
        return driver.AMQPDriver(self._config)

    def _get_postprocessor(self):
        return postprocessor.PostProcessor(self._get_driver(),
                                           self._discovery)

    def __getattr__(self, item):
        if isinstance(self._source, entry_point.EntryPoint):
            source = self._source
        else:
            source = entry_point.EntryPointFactory().create(self._source)

        postproc = self._get_postprocessor()
        proxy = proxies.RPCProxy(postproc, source,
                                 context=self._context, headers=self._headers)
        return getattr(proxy, item)
