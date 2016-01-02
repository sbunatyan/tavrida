import abc
import logging

from amqp_driver import driver as amqp_driver
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
