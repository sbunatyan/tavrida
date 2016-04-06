import logging

import pika

import base
from tavrida import exceptions
from tavrida import messages


class BasePikaAsync(base.AbstractClient):

    def __init__(self, config):

        self._connection = None
        self._channel = None
        self._closing = False
        self._stopping = False
        self._config = config.to_pika_params()
        self.log = logging.getLogger(__name__)
        super(BasePikaAsync, self).__init__(config)

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_on_close to False, which is not the default
        behavior of this adapter.

        :rtype: pika.SelectConnection

        """
        return pika.SelectConnection(self._config,
                                     self.on_connection_open,
                                     stop_ioloop_on_close=False)

    def on_connection_open(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection

        """
        self._add_on_connection_close_callback()
        self.open_channel()

    def _add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        self._connection.add_on_close_callback(self._on_connection_closed)

    def _on_connection_closed(self, connection, reply_code, reply_text):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            self.log.warning('Connection closed, trying to reconnect')
            self._connection.add_timeout(self._config.retry_delay,
                                         self.reconnect)

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()
        if not self._closing:
            if self._if_do_retry():
                self._current_reconnect_attempt += 1
                # Create a new connection
                self._connection = self.connect()
                # There is now a new connection, needs a new ioloop to run
                self._connection.ioloop.start()
            else:
                self.log.error("Connection closed unexpectedly")

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        self._channel = channel
        self._add_on_channel_close_callback()

    def _add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        self._channel.add_on_close_callback(self._on_channel_closed)

    def _on_channel_closed(self, channel, reply_code, reply_text):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed

        """
        if not self._closing:
            self._connection.close()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        if self._channel:
            self._channel.close()

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        if self._connection:
            self._connection.close()


class Reader(BasePikaAsync, base.AbstractReader):
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """
    EXCHANGE = 'message'
    EXCHANGE_TYPE = 'topic'
    QUEUE = 'text'
    ROUTING_KEY = 'example.text'

    def __init__(self, config, queue, preprocessor):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str amqp_url: The AMQP url to connect with

        """
        super(Reader, self).__init__(config)
        self._connection = None
        self._channel = None
        self._consumer_tag = None
        self._config = config.to_pika_params()
        self.log = logging.getLogger(__name__)
        self._queue = queue
        self.preprocessor = preprocessor

    def create_queue(self):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        QueueCreator(self._config, self._queue).create_queue()

    def _add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        self._channel.add_on_close_callback(self._on_channel_closed)
        self._start_consuming()

    def bind_queue(self, exchange_name, routing_key):
        BindingCreator(
            self._config,
            self._queue,
            exchange_name,
            routing_key).create_binding()

    def _start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        self._add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self._queue)

    def _add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        self._channel.add_on_cancel_callback(self._on_consumer_cancelled)

    def _on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        """
        msg = messages.AMQPMessage(body, properties.headers)
        self._on_message(msg, basic_deliver)

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

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            self._channel.basic_cancel(self._on_cancelok, self._consumer_tag)

    def _on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame

        """
        self.close_channel()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        self.log.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self.close_channel()
        self.close_connection()
        self._connection.ioloop.stop()
        self.log.info('Stopped')

    def create_exchange(self, exchange_name, ex_type):
        ExchangeCreator(self._config, exchange_name, ex_type).create_exchange()

    def publish_message(self, exchange, routing_key, message):
        props = pika.BasicProperties(headers=message.headers)
        self._channel.basic_publish(exchange=exchange,
                                    routing_key=routing_key,
                                    body=message.body,
                                    properties=props)


class Writer(BasePikaAsync, base.AbstractWriter):

    def __init__(self, config):
        super(Writer, self).__init__(config)
        self._config = config.to_pika_params()
        self.log = logging.getLogger(__name__)
        self._connection = None
        self._channel = None
        self._closing = False
        self._stopping = False
        self._publish_interval = 0

    def stop(self):
        """Stop the example by closing the channel and connection. We
        set a flag here so that we stop scheduling new messages to be
        published. The IOLoop is started because this method is
        invoked by the Try/Catch below when KeyboardInterrupt is caught.
        Starting the IOLoop again will allow the publisher to cleanly
        disconnect from RabbitMQ.

        """
        self.log.info('Stopping')
        self._stopping = True
        self.close_channel()
        self.close_connection()
        self._connection.ioloop.start()
        self.log.info('Stopped')

    def create_exchange(self, exchange_name, ex_type):
        ExchangeCreator(self._config, exchange_name, ex_type).create_exchange()

    def publish_message(self, exchange, routing_key, message):
        Publisher(self._config, exchange, routing_key, message)\
            .publish_message()


class Publisher(object):

    def __init__(self, config, exchange_name, routing_key, message):
        self._config = config
        self._exchange_name = exchange_name
        self._routing_key = routing_key
        self._message = message
        self.log = logging.getLogger(__name__)

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_on_close to False, which is not the default
        behavior of this adapter.

        :rtype: pika.SelectConnection

        """
        return pika.SelectConnection(self._config,
                                     self._open_channel,
                                     stop_ioloop_on_close=False)

    def _open_channel(self, unused_connection):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        self._channel = channel
        self._publish_message()

    def _publish_message(self):
        props = pika.BasicProperties(headers=self._message.headers)
        self._channel.basic_publish(exchange=self._exchange_name,
                                    routing_key=self._routing_key,
                                    body=self._message.body,
                                    properties=props)
        self.close_connection()
        self._connection.ioloop.stop()

    def publish_message(self):
        self._connection = self.connect()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        if self._connection:
            self._connection.close()
            self._connection.ioloop.stop()


class ExchangeCreator(object):

    def __init__(self, config, exchange_name, ex_type):
        self._config = config
        self._exchange_name = exchange_name
        self._ex_type = ex_type
        self.log = logging.getLogger(__name__)

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_on_close to False, which is not the default
        behavior of this adapter.

        :rtype: pika.SelectConnection

        """
        return pika.SelectConnection(self._config,
                                     self._open_channel,
                                     stop_ioloop_on_close=False)

    def _open_channel(self, unused_connection):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        self.log.info('Creating a new channel')
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        self._channel = channel
        self._create_exchange()

    def _create_exchange(self):
        self._channel.exchange_declare(self._on_exchange_declareok,
                                       self._exchange_name,
                                       self._ex_type,
                                       durable=True)

    def _on_exchange_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response
                                               frame

        """
        self.close_connection()
        self._connection.ioloop.stop()

    def create_exchange(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        if self._connection:
            self._connection.close()


class QueueCreator(object):

    def __init__(self, config, queue_name):
        self._config = config
        self._queue = queue_name
        self.log = logging.getLogger(__name__)

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_on_close to False, which is not the default
        behavior of this adapter.

        :rtype: pika.SelectConnection

        """
        return pika.SelectConnection(self._config,
                                     self._open_channel,
                                     stop_ioloop_on_close=False)

    def _open_channel(self, unused_connection):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        self._channel = channel
        self._create_queue()

    def _create_queue(self):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        self._channel.queue_declare(self._on_queue_declareok,
                                    self._queue,
                                    durable=True)

    def _on_queue_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response
                                               frame

        """
        self.close_connection()
        self._connection.ioloop.stop()

    def create_queue(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        self._connection.close()


class BindingCreator(object):

    def __init__(self, config, queue_name, exchange_name, routing_key):
        self._config = config
        self._queue = queue_name
        self._exchange_name = exchange_name
        self._routing_key = routing_key
        self.log = logging.getLogger(__name__)
        print self._queue

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika. If you want the reconnection to work, make
        sure you set stop_ioloop_on_close to False, which is not the default
        behavior of this adapter.

        :rtype: pika.SelectConnection

        """
        return pika.SelectConnection(self._config,
                                     self._open_channel,
                                     stop_ioloop_on_close=False)

    def _open_channel(self, unused_connection):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        self._channel = channel
        self._create_binding()

    def _create_binding(self):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        self._channel.queue_bind(self._on_binding_declareok, self._queue,
                                 self._exchange_name, self._routing_key)

    def _on_binding_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response
                                               frame

        """
        self.close_connection()
        self._connection.ioloop.stop()

    def create_binding(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        if self._connection:
            self._connection.close()
