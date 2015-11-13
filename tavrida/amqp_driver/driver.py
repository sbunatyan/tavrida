import pika_amqp


from tavrida import exceptions


class AMQPDriver(object):

    def __init__(self, amqp_library_name):
        if amqp_library_name == "pika":
            self._amqp = pika_amqp
        else:
            raise exceptions.IncorrectAMQPLibrary

    def get_reader(self, config, queue, preprocessor=None):
        return self._amqp.Reader(config, queue, preprocessor)

    def get_writer(self, config):
        return self._amqp.Writer(config)

    def create_queue(self, config, queue):
        reader = self.get_reader(config, queue)
        reader.connect()
        reader.create_queue()
        reader.close_connection()

    def create_exchange(self, config, exchange_name):
        writer = self.get_writer(config)
        writer.connect()
        writer.create_exchange(exchange_name, "topic")
        writer.close_connection()

    def bind_queue(self, config, queue, exchange, service_name):
        routing_key = service_name + ".#"
        reader = self.get_reader(config, queue)
        reader.connect()
        reader.bind_queue(exchange, routing_key)
        reader.close_connection()
