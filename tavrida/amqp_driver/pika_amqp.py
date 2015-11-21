import logging
import time

import pika

import base
from tavrida import exceptions
from tavrida import messages


class Reader(base.AbstractReader):

    def __init__(self, config, queue, preprocessor):
        self.log = logging.getLogger(__name__)
        self._config = config.to_pika_params()
        self._queue = queue
        self._connection = None
        self._channel = None
        self.preprocessor = preprocessor

    def connect(self):
        self._connection = pika.BlockingConnection(self._config)
        self._channel = self._connection.channel()

    def run(self):
        try:
            self.connect()
            for frame, properties, body in self._channel.consume(self._queue):
                msg = messages.AMQPMessage(body, properties.headers)
                self._on_message(msg, frame)
        except (pika.exceptions.ConnectionClosed,
                pika.exceptions.AMQPConnectionError) as e:
            self.log.error(e)
            time.sleep(self._config.retry_delay)
            self.run()

    def _on_message(self, msg, frame):
        try:
            self.preprocessor.process(msg)
        except Exception as e:
            self.log.exception(e)
            if not isinstance(e, exceptions.BaseException):
                self._channel.basic_ack(frame.delivery_tag)
            elif not isinstance(e, exceptions.AckableException):
                self._channel.basic_reject(frame.delivery_tag)
            else:
                self._channel.basic_ack(frame.delivery_tag)
        else:
            self._channel.basic_ack(frame.delivery_tag)

    def close_connection(self):
        self._channel.close()
        self._connection.close()

    def stop(self):
        self.close_connection()

    def create_queue(self):
        self._channel.queue_declare(queue=self._queue, durable=True)

    def bind_queue(self, exchange_name, routing_key):
        self._channel.queue_bind(queue=self._queue,
                                 exchange=exchange_name,
                                 routing_key=routing_key)


class Writer(base.AbstractWriter):

    def __init__(self, config):
        self.log = logging.getLogger(__name__)
        self._config = config.to_pika_params()
        self._connection = None
        self._channel = None

    def connect(self):
        try:
            self._connection = pika.BlockingConnection(self._config)
            self._channel = self._connection.channel()
        except (pika.exceptions.ConnectionClosed,
                pika.exceptions.AMQPConnectionError) as e:
            self.log.error(e)
            time.sleep(self._config.retry_delay)
            self.connect()

    def close_connection(self):
        self._channel.close()
        self._connection.close()

    def publish_message(self, exchange, routing_key, message):
        props = pika.BasicProperties(headers=message.headers)
        self._channel.basic_publish(exchange=exchange,
                                    routing_key=routing_key,
                                    body=message.body,
                                    properties=props)

    def create_exchange(self, exchange_name, ex_type):
        self._channel.exchange_declare(exchange=exchange_name,
                                       type=ex_type,
                                       durable=True)
