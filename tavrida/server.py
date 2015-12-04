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
        rt = self._get_router()
        disc = self._get_discovery()

        pub_services = rt.subscription_lookup(service_cls)
        for pub_service in pub_services:
            subscriptions = service_cls.get_subscription().subscriptions
            for pub_method in subscriptions.keys():
                ep = entry_point.Source(pub_service, pub_method)
                exchange_name = disc.get_remote_publisher(ep.service)
                driver.bind_queue(self._queue_name,
                                  exchange_name, ep.to_routing_key())

    def _create_notification_exchanges(self):
        disc = self._get_discovery()
        disc.get_all_exchanges()
        driver = self._driver
        for exc_type, exchange_names in disc.get_all_exchanges().iteritems():
            for exchange_name in exchange_names:
                driver.create_exchange(exchange_name)

    def _create_service_structures(self, service_cls):
        driver = self._driver
        rt = self._get_router()
        service_names = rt.reverse_lookup(service_cls)
        for service_name in service_names:
            driver.bind_queue(self._queue_name,
                              self._exchange_name, service_name)
            if service_cls.get_subscription().subscriptions:
                self._create_subscription_binding(service_cls)

    def _create_amqp_structures(self):
        driver = self._driver
        driver.create_exchange(self._exchange_name)
        driver.create_queue(self._queue_name)

        self._create_notification_exchanges()

        for service_cls in self._service_list:
            self._create_service_structures(service_cls)

    def _get_driver(self):
        if not self._config:
            raise exceptions.IncorrectAMQPConfig(ampq_url=self._config)
        driver = amqp_driver.AMQPDriver(self._config)
        return driver

    def _get_discovery(self):
        return self._get_postprocessor().discovery_service

    def _get_processor(self, services):
        return processor.Processor(services)

    def _get_postprocessor(self, discovery_service=None):
        if not discovery_service:
            discovery_service = discovery.LocalDiscovery()
        return postprocessor.PostProcessor(self._driver,
                                           discovery_service)

    def _get_preprocessor(self):
        processor_instance = self._get_processor(self._services)
        postprocessor_instance = self._get_postprocessor()
        return preprocessor.PreProcessor(processor_instance,
                                         postprocessor_instance)

    def _instantiate_services(self):
        preproc = self._get_preprocessor()
        for s in self._service_list:
            self.log.info("Service %s", s.__name__)
            self._services.append(s(preproc, preproc.postprocessor))

    def run(self):
        self.log.info("Instantiating service classes")
        self._instantiate_services()
        self.log.info("Creating AMQP structures on Server")
        self._create_amqp_structures()
        self.log.info("Starting server on %s: %s", self._config.host,
                      self._config.port)
        self.log.info("---------------------------")
        self._driver.listen(queue=self._queue_name,
                            preprocessor=self._get_preprocessor())
