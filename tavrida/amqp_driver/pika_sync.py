import abc
import logging
import time

import pika

import base
from tavrida import exceptions
from tavrida import messages


class PikaClient(base.AbstractClient):

    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        super(PikaClient, self).__init__(config)
        self._connection = None
        self._channel = None

    def close_connection(self):
        if self._channel:
            self._channel.close()
        if self._connection:
            self._connection.close()


class Reader(PikaClient, base.AbstractReader):

    def __init__(self, config, queue, preprocessor):
        super(Reader, self).__init__(config)
        self._config = config.to_pika_params()
        self.log = logging.getLogger(__name__)
        self._queue = queue
        self._channel = None
        self.preprocessor = preprocessor

    def connect(self):
        if not self._connection:
            self._connection = pika.BlockingConnection(self._config)
        if not self._channel:
            self._channel = self._connection.channel()

    def run(self):
        try:
            self.connect()
            for frame, properties, body in self._channel.consume(self._queue):
                msg = messages.AMQPMessage(body, properties.headers)
                self._on_message(msg, frame)
        except (pika.exceptions.ConnectionClosed,
                pika.exceptions.AMQPConnectionError) as e:
            self._connection = None
            self._channel = None
            self.log.error(e)
            time.sleep(self._config.retry_delay)
            if self._if_do_retry():
                self._current_reconnect_attempt += 1
                self.run()

    def _ack(self, frame):
        self.log.debug("Starting ack frame with delivery tag %s",
                       frame.delivery_tag)
        self._channel.basic_ack(frame.delivery_tag)
        self.log.debug("Acked frame with delivery tag %s",
                       frame.delivery_tag)

    def _reject(self, frame):
        self.log.debug("Starting reject frame with delivery tag %s",
                       frame.delivery_tag)
        self._channel.basic_reject(frame.delivery_tag)
        self.log.debug("Rejected frame with delivery tag %s",
                       frame.delivery_tag)

    def _on_message(self, msg, frame):
        try:
            self.preprocessor.process(msg)
        except Exception as e:
            self.log.exception(e)
            if isinstance(e, exceptions.NackableException):
                self._reject(frame)
            else:
                self._ack(frame)
        else:
            self._ack(frame)

    def stop(self):
        self.close_connection()

    def create_queue(self):
        self.connect()
        try:
            self._channel.queue_declare(queue=self._queue, durable=True)
        finally:
            self.close_connection()

    def bind_queue(self, exchange_name, routing_key):
        self.connect()
        try:
            self._channel.queue_bind(queue=self._queue,
                                     exchange=exchange_name,
                                     routing_key=routing_key)
        finally:
            self.close_connection()

    def publish_message(self, exchange, routing_key, message):
        self.connect()
        props = pika.BasicProperties(headers=message.headers)
        self._channel.basic_publish(exchange=exchange,
                                    routing_key=routing_key,
                                    body=message.body,
                                    properties=props)


class Writer(PikaClient, base.AbstractWriter):

    def __init__(self, config):
        super(Writer, self).__init__(config)
        self._config = config.to_pika_params()
        self.log = logging.getLogger(__name__)
        self._channel = None

    def connect(self):
        try:
            self._connection = pika.BlockingConnection(self._config)
            self._channel = self._connection.channel()
        except (pika.exceptions.ConnectionClosed,
                pika.exceptions.AMQPConnectionError) as e:
            if self._if_do_retry():
                self._current_reconnect_attempt += 1
                self.log.error(e)
                time.sleep(self._config.retry_delay)
                self.connect()
            else:
                raise

    def publish_message(self, exchange, routing_key, message):
        self.connect()
        try:
            props = pika.BasicProperties(headers=message.headers)
            self._channel.basic_publish(exchange=exchange,
                                        routing_key=routing_key,
                                        body=message.body,
                                        properties=props)
        finally:
            self.close_connection()

    def create_exchange(self, exchange_name, ex_type):
        self.connect()
        try:
            self._channel.exchange_declare(exchange=exchange_name,
                                           type=ex_type,
                                           durable=True)
        finally:
            self.close_connection()
