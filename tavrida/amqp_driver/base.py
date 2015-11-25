import abc


class AbstractClient(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        super(AbstractClient, self).__init__()
        self._reconnect_attempts = config.reconnect_attempts
        self._current_reconnect_attempt = 0
        self._connection = None

    def _if_do_retry(self):
        return (self._reconnect_attempts < 0 or
                (self._reconnect_attempts >= 0 and
                 self._current_reconnect_attempt < self._reconnect_attempts))

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
