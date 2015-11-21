import copy

from tavrida.amqp_driver import driver
from tavrida import discovery
from tavrida import entry_point
from tavrida import postprocessor
from tavrida import proxies


class RPCClient(object):

    def __init__(self, config, service, exchange=None, source="",
                 discovery=None, headers=None):
        self._config = config
        self._service = service
        self._exchange = exchange
        self._source = source
        self._headers = copy.copy(headers) or {}

        if exchange and discovery:
            raise ValueError("You should define either discovery or exchange "
                             "but not both")

        if exchange:
            self._discovery = self._get_discovery()
            self._discovery.register_remote_service(self._service,
                                                    self._exchange)
        else:
            self._discovery = discovery

    def _get_discovery(self):
        return discovery.LocalDiscovery()

    def _get_writer(self):
        return driver.AMQPDriver("pika").get_writer(self._config)

    def _get_postprocessor(self):
        return postprocessor.PostProcessor(self._get_writer(),
                                           self._discovery)

    def __getattr__(self, item):
        if isinstance(self._source, entry_point.EntryPoint):
            source = self._source
        else:
            source = entry_point.EntryPointFactory().create(self._source)

        postproc = self._get_postprocessor()
        proxy = proxies.RPCServiceProxy(postproc, self._service, source,
                                        headers=self._headers)
        return getattr(proxy, item)
