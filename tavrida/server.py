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
import logging
import sys

from amqp_driver import driver as amqp_driver
import config
import configfile
import discovery
import exceptions
import postprocessor
import preprocessor
import router


class Server(object):

    """
    Server start multiple services.
    Before start it creates all AMQP structures for each service
    (queue, exchanges, bindings) in RabbitMQ
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, config, queue_name, exchange_name, service_list):
        super(Server, self).__init__()
        self.log = logging.getLogger(__name__)
        self._config = config
        self._service_list = (service_list if isinstance(service_list, list)
                              else [service_list])
        self._queue_name = queue_name
        self._exchange_name = exchange_name
        self._services = []
        self._driver = self._get_driver()

    @property
    def queue_name(self):
        return self._queue_name

    @property
    def exchange_name(self):
        return self._exchange_name

    def _get_router(self):
        return router.Router()

    def _create_subscription_binding(self, service_cls):
        driver = self._driver
        disc = service_cls.get_discovery()
        disp = service_cls.get_dispatcher()

        publishers = disp.get_publishers()
        for publisher in publishers:
            exchange_name = disc.get_remote_publisher(publisher.service)
            driver.bind_queue(self._queue_name,
                              exchange_name, publisher.to_routing_key())

    def _create_notification_exchanges(self, service_cls):
        disc = service_cls.get_discovery()
        disc.get_all_exchanges()
        driver = self._driver
        for exc_type, exchange_names in disc.get_all_exchanges().iteritems():
            for exchange_name in exchange_names:
                driver.create_exchange(exchange_name)

    def _create_service_structures(self, service_cls):
        driver = self._driver
        disp = service_cls.get_dispatcher()

        service_names = disp.get_request_entry_services()
        for service_name in service_names:
            driver.bind_queue(self._queue_name,
                              self._exchange_name, service_name)
            if service_cls.get_dispatcher().subscriptions:
                self._create_subscription_binding(service_cls)

    def _create_amqp_structures(self):
        driver = self._driver
        driver.create_exchange(self._exchange_name)
        driver.create_queue(self._queue_name)

        for service_cls in self._service_list:
            self._create_service_structures(service_cls)
            self._create_notification_exchanges(service_cls)

    def _get_driver(self):
        if not self._config:
            raise exceptions.IncorrectAMQPConfig(ampq_url=self._config)
        driver = amqp_driver.AMQPDriver(self._config)
        return driver

    def _get_preprocessor(self):
        return preprocessor.PreProcessor(self._get_router(),
                                         self._services)

    def _instantiate_services(self):
        for s in self._service_list:
            self.log.info("Service %s", s.__name__)
            postproc = postprocessor.PostProcessor(self._driver,
                                                   s.get_discovery())
            self._services.append(s(postproc))

    def run(self):
        """
        Starts to listen RabbitMQ.
        Before listening instantiates service objects and creates AMQP
        structures in RabbitMQ
        """
        self.log.info("Instantiating services")
        self._instantiate_services()
        self.log.info("Creating AMQP structures on Server")
        self._create_amqp_structures()
        self.log.info("Server is listening on %s: %s", self._config.host,
                      self._config.port)
        self._driver.listen(queue=self._queue_name,
                            preprocessor=self._get_preprocessor())


class CLIServer(Server):

    """
    CLIServer reads config file to obtain all required settings.
    It automatically creates all config objects and binds discovery services
    to controller classes.
    """

    def __init__(self, config_file=None, project_name=None):
        configfile.get_config(sys.argv[1:], project_name=project_name,
                              config_file=config_file)
        conf = configfile.CONF
        credentials = config.Credentials(username=conf.connection.username,
                                         password=conf.connection.password)
        ssl_opts = None
        if conf.ssl:
            ssl_opts = {
                "keyfile": conf.ssl.keyfile,
                "certfile": conf.ssl.certfile,
                "server_side": False,
                "cert_reqs": conf.ssl.cert_reqs,
                "ssl_version": conf.ssl.ssl_version,
                "ca_certs": conf.ssl.ca_certs,
                "suppress_ragged_eofs": conf.ssl.suppress_ragged_eofs,
                "ciphers": conf.ssl.ciphers,
            }
        conn_conf = config.ConnectionConfig(
            host=conf.connection.host,
            credentials=credentials,
            port=conf.connection.port,
            virtual_host=conf.connection.virtual_host,
            channel_max=conf.connection.channel_max,
            frame_max=conf.connection.frame_max,
            heartbeat_interval=conf.connection.heartbeat_interval,
            ssl=conf.connection.ssl,
            ssl_options=ssl_opts,
            connection_attempts=conf.connection.connection_attempts,
            retry_delay=conf.connection.retry_delay,
            socket_timeout=conf.connection.socket_timeout,
            locale=conf.connection.locale,
            backpressure_detection=conf.connection.backpressure_detection,
            reconnect_attempts=conf.connection.reconnect_attempts,
            async_engine=conf.connection.async_engine
        )

        service_list = configfile.get_services_classes()
        service_mapping = configfile.get_service_name_class_mapping()
        print configfile.get_services()
        for service in configfile.get_services():
            df = discovery.DiscoveryFactory(service["discovery"])
            disc = df.get_discovery_service(service["name"],
                                            service.get("subscriptions"))
            service_mapping[service["name"]].set_discovery(disc)

        super(CLIServer, self).__init__(
            conn_conf,
            queue_name=conf.server.queue_name,
            exchange_name=conf.server.exchange_name,
            service_list=service_list)


