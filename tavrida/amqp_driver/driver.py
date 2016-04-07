import pika_async
import pika_sync


class AMQPDriver(object):

    def __init__(self, config):
        if not config.async_engine:
            self._engine = pika_sync
        else:
            self._engine = pika_async
        self._config = config
        self._reader = None
        self._writer = None

    def create_reader(self, queue, preprocessor=None):
        return self._engine.Reader(self._config, queue, preprocessor)

    def create_writer(self):
        return self._engine.Writer(self._config)

    def _get_blocking_writer(self):
        return pika_sync.Writer(self._config)

    def _get_blocking_reader(self, queue, preprocessor=None):
        return pika_sync.Reader(self._config, queue, preprocessor)

    def create_queue(self, queue):
        reader = self._get_blocking_reader(queue)
        reader.create_queue()

    def create_exchange(self, exchange_name):
        writer = self._get_blocking_writer()
        writer.create_exchange(exchange_name, "topic")

    def bind_queue(self, queue, exchange, service_name):
        routing_key = service_name + ".#"
        reader = self._get_blocking_reader(queue)
        reader.bind_queue(exchange, routing_key)

    def publish_message(self, exchange, routing_key, message):
        if self._reader:
            self._writer = self._reader
        else:
            self._writer = self.create_writer()
        self._writer.publish_message(exchange, routing_key, message)

    def listen(self, queue, preprocessor=None):
        reader = self.create_reader(queue, preprocessor)
        self._reader = reader
        reader.run()

    @property
    def reader(self):
        return self._reader

    @property
    def writer(self):
        return self._writer
