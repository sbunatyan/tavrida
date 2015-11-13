import abc


class AbstractClient(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def close_connection(self):
        pass


class AbstractReader(AbstractClient):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass

    @abc.abstractmethod
    def _on_message(self, message):
        pass

    @abc.abstractmethod
    def create_queue(self):
        pass

    @abc.abstractmethod
    def bind_queue(self, exchange_name, routing_key):
        pass


class AbstractWriter(AbstractClient):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def publish_message(self, exchange, routing_key, message):
        pass

    @abc.abstractmethod
    def create_exchange(self, exchange_name, ex_type):
        pass
