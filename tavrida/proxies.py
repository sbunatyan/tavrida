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

import entry_point
import messages


class RCPCallProxy(object):

    """
    Proxy class for method call
    """

    def __init__(self, postprocessor, service_name, method_name, source,
                 context, correlation_id, headers, kwargs):
        super(RCPCallProxy, self).__init__()
        self._postprocessor = postprocessor
        self._service_name = service_name
        self._method_name = method_name
        self._source = source
        self._context = context
        self._correlation_id = correlation_id
        self._headers = copy.copy(headers) or {}
        self._kwargs = kwargs

    def _make_request(self, context="", correlation_id="", reply_to="",
                      source=""):
        if not source:
            source = self._source

        if not context:
            context = self._context

        if not correlation_id:
            correlation_id = self._correlation_id

        if not reply_to and not isinstance(reply_to, entry_point.EntryPoint):
            reply_to = source.service

        payload = self._kwargs
        dst = entry_point.Destination(self._service_name, self._method_name)
        headers = {
            "correlation_id": correlation_id,
            "reply_to": str(reply_to),
            "source": str(source),
            "destination": str(dst)
        }

        request_headers = self._headers.copy()
        request_headers.update(headers)
        request = messages.Request(request_headers, context, payload)
        return request

    def call(self, correlation_id="", context="", reply_to="", source=""):
        """
        Executes

        :param reply_to:
        :param source:
        :return:
        """
        request = self._make_request(context=context,
                                     correlation_id=correlation_id,
                                     reply_to=reply_to,
                                     source=source)
        self._postprocessor.process(request)

    def cast(self, correlation_id="", context="", source=""):
        request = self._make_request(context=context,
                                     correlation_id=correlation_id,
                                     reply_to=entry_point.NullEntryPoint(),
                                     source=source)
        self._postprocessor.process(request)

    def transfer(self, request, context="", reply_to="", source=""):
        if request.context:
            context = context or {}
            context.update(request.context)
        request = self._make_request(correlation_id=request.correlation_id,
                                     reply_to=reply_to,
                                     context=context,
                                     source=source)
        self._postprocessor.process(request)


class RPCMethodProxy(object):

    def __init__(self, postprocessor, service_name, method_name, source,
                 context="", correlation_id="", headers=""):
        self._postprocessor = postprocessor
        self._service_name = service_name
        self._method_name = method_name
        self._source = source
        self._context = context
        self._correlation_id = correlation_id
        self._headers = copy.copy(headers)

    def __call__(self, **kwargs):
        self._kwargs = kwargs
        return RCPCallProxy(self._postprocessor, self._service_name,
                            self._method_name, self._source, self._context,
                            self._correlation_id, self._headers, kwargs)


class RPCServiceProxy(object):

    def __init__(self, postprocessor, name, source, context=None,
                 correlation_id="", headers=None):
        self._postprocessor = postprocessor
        self._name = name
        self._source = source
        self._context = context
        self._correlation_id = correlation_id
        self._headers = copy.copy(headers)

    def __getattr__(self, item):
        return RPCMethodProxy(self._postprocessor, self._name, item,
                              self._source, self._context,
                              self._correlation_id, self._headers)


class RPCProxy(object):

    def __init__(self, postprocessor, source, context=None,
                 correlation_id="", headers=None):
        self._postprocessor = postprocessor
        self._source = source
        self._context = context
        self._correlation_id = correlation_id
        self._headers = copy.copy(headers) or {}

    def _get_discovery_service(self):
        return self._postprocessor.discovery_service

    def __getattr__(self, item):
        disc = self._get_discovery_service()
        disc.get_remote(item)
        return RPCServiceProxy(self._postprocessor, item, self._source,
                               self._context, self._correlation_id)

    def add_headers(self, headers):
        self._headers = copy.copy(headers)

    def publish(self, correlation_id="", **kwargs):
        headers = {
            "correlation_id": correlation_id or self._correlation_id,
            "source": str(self._source)
        }
        notification_headers = self._headers.copy()
        notification_headers.update(headers)
        publication = messages.Notification(notification_headers,
                                            self._context, kwargs)
        self._postprocessor.process(publication)
