#!/usr/bin/env python
# Copyright (c) 2014 Eugene Frolov <eugene@frolov.net.ru>
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

from distutils import core

core.setup(
    name='tavrida',
    packages=['tavrida'],
    version='1.0.0',
    description="RPC and Pub/Sub over RabbitMQ",
    author="Sergey Bunatyan",
    author_email="sergey@bunatian.ru",
    url="https://github.com/sbunatyan/tavrida",
    download_url="https://github.com/sbunatyan/tavrida/tree/1.0.0",
    keywords=["amqp", "prc", "tavrida", "rabbitmq"])
