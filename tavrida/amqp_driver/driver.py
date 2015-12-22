import pika_amqp
import pika_aync


class AMQPDriver(object):

    def __init__(self, config):
        if not config.async_engine:
            self._amqp = pika_amqp
        else:
            self._amqp = pika_aync
        self._config = config
        self._reader = None

    def get_reader(self, queue, preprocessor=None):
        return self._amqp.Reader(self._config, queue, preprocessor)

    def get_writer(self):
        return self._amqp.Writer(self._config)

    def _get_blocking_writer(self):
        return pika_amqp.Writer(self._config)

    def _get_blocking_reader(self, queue, preprocessor=None):
        return pika_amqp.Reader(self._config, queue, preprocessor)

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
            self._reader.publish_message(exchange, routing_key, message)
        else:
            writer = self.get_writer()
            writer.publish_message(exchange, routing_key, message)

    def listen(self, queue, preprocessor=None):
        reader = self.get_reader(queue, preprocessor)
        self._reader = reader
        reader.run()
