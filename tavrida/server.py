import abc
import logging

from amqp_driver import driver as amqp_driver
import discovery
import entry_point
import exceptions
import postprocessor
import preprocessor
import processor
import router


class Server(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, config, queue_name, exchange_name, service_list):
        self.log = logging.getLogger(__name__)
        self._config = config
        self._service_list = (service_list if isinstance(service_list, list)
                              else [service_list])
        self._reader = None
        self._writer = None
        self._queue_name = queue_name
        self._exchange_name = exchange_name
        self._services = []

    @property
    def queue_name(self):
        return self._queue_name

    @property
    def exchange_name(self):
        return self._exchange_name

    def _get_amqp_driver(self):
        return amqp_driver.AMQPDriver("pika")

    def _get_router(self):
        return router.Router()

    def _create_subscription_binding(self, service_cls):
        driver = self._get_amqp_driver()
        rt = self._get_router()
        disc = self._get_discovery()

        pub_service = rt.subscription_lookup(service_cls)
        subscriptions = service_cls.get_subscription().subscriptions
        for pub_method in subscriptions.keys():
            ep = entry_point.Source(pub_service, pub_method)
            exchange_name = disc.get_remote_publisher(ep.service)
            driver.bind_queue(self._config, self._queue_name,
                              exchange_name, ep.to_routing_key())

    def _create_notification_exchanges(self):
        disc = self._get_discovery()
        disc.get_all_exchanges()
        driver = self._get_amqp_driver()
        for exc_type, exchange_names in disc.get_all_exchanges().iteritems():
            for exchange_name in exchange_names:
                driver.create_exchange(self._config, exchange_name)

    def _create_service_structures(self, service_cls):
        driver = self._get_amqp_driver()
        rt = self._get_router()
        service_name = rt.reverse_lookup(service_cls)
        driver.bind_queue(self._config, self._queue_name,
                          self._exchange_name, service_name)
        if service_cls.get_subscription().subscriptions:
            self._create_subscription_binding(service_cls)

    def _create_amqp_structures(self):
        driver = self._get_amqp_driver()
        driver.create_exchange(self._config, self._exchange_name)
        driver.create_queue(self._config, self._queue_name)

        self._create_notification_exchanges()

        for service_cls in self._service_list:
            self._create_service_structures(service_cls)

    def _get_reader(self):
        if self._reader:
            return self._reader

        if not self._config:
            raise exceptions.IncorrectAMQPConfig(ampq_url=self._config)

        preproc = self._get_preprocessor()
        return self._get_amqp_driver().get_reader(self._config,
                                                  self._queue_name,
                                                  preprocessor=preproc)

    def _get_writer(self):
        if self._writer:
            return self._writer

        if not self._config:
            raise exceptions.IncorrectAMQPConfig(ampq_url=self._config)
        writer = self._get_amqp_driver().get_writer(self._config)
        return writer

    def _get_discovery(self):
        return self._get_postprocessor().discovery_service

    def _get_processor(self, services):
        return processor.Processor(services)

    def _get_postprocessor(self, discovery_service=None):
        if not discovery_service:
            discovery_service = discovery.LocalDiscovery()
        return postprocessor.PostProcessor(self._get_writer(),
                                           discovery_service)

    def _get_preprocessor(self):
        if not self._services:
            raise exceptions.ServicesNotInstantiated
        processor_instance = self._get_processor(self._services)
        postprocessor_instance = self._get_postprocessor()
        return preprocessor.PreProcessor(processor_instance,
                                         postprocessor_instance)

    def _instantiate_services(self):
        postproc = self._get_postprocessor()
        for s in self._service_list:
            self.log.info("Service %s", s.__name__)
            self._services.append(s(postproc))

    def run(self):
        self.log.info("Instantiating service classes")
        self._instantiate_services()
        self._reader = self._get_reader()
        self.log.info("Creating AMQP structures on Server")
        self._create_amqp_structures()
        self.log.info("Starting server on %s: %s", self._config.host,
                      self._config.port)
        self.log.info("---------------------------")
        self._reader.run()

    def stop(self):
        self._reader.close_connection()
