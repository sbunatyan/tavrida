import pika_amqp
import pika_aync

from tavrida import exceptions


class AMQPDriver(object):

    def __init__(self, config):
        if not config.async_engine:
            self._amqp = pika_amqp
        else:
            raise exceptions.IncorrectAMQPLibrary
        self._config = config

    def get_reader(self, queue, preprocessor=None):
        return self._amqp.Reader(self._config, queue, preprocessor)

    def get_writer(self):
        return self._amqp.Writer(self._config)

    def create_queue(self, queue):
        reader = self.get_reader(queue)
        reader.create_queue()

    def create_exchange(self, exchange_name):
        writer = self.get_writer()
        writer.create_exchange(exchange_name, "topic")

    def bind_queue(self, queue, exchange, service_name):
        routing_key = service_name + ".#"
        reader = self.get_reader(queue)
        reader.bind_queue(exchange, routing_key)

    def publish_message(self, exchange, routing_key, message):
        writer = self.get_writer()
        writer.publish_message(exchange, routing_key, message)

    def listen(self, queue, preprocessor=None):
        reader = self.get_reader(queue, preprocessor)
        reader.run()
