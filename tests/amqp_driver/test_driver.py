import unittest

import mock

from tavrida import config
from tavrida.amqp_driver import driver
from tavrida.amqp_driver import pika_sync
from tavrida.amqp_driver import pika_async


class AMQPDriverSyncAndAsyncTestCase(unittest.TestCase):

    def setUp(self):
        super(AMQPDriverSyncAndAsyncTestCase, self).setUp()
        self.user = "user"
        self.password = "password"
        self.credentials = config.Credentials(self.user, self.password)
        self.host = "host"

    def test_driver_uses_pika_sync_engine(self):

        """
        Tests that driver uses sync amqp engine if async_engine parameter=False
         in config object
        """
        conf = config.ConnectionConfig(self.host, self.credentials)
        drvr = driver.AMQPDriver(conf)
        self.assertEqual(drvr._engine, pika_sync)

    @mock.patch.object(pika_sync, "Reader")
    def test_get_reader_for_sync_engine(self, engine_mock):

        """
        Tests that driver uses Reader of sync engine
        """

        conf = config.ConnectionConfig(self.host, self.credentials)
        drvr = driver.AMQPDriver(conf)
        queue = "queue_name"
        preprocessor = mock.Mock()
        reader = drvr.get_reader(queue, preprocessor)
        self.assertEqual(reader, engine_mock())

    @mock.patch.object(pika_sync, "Writer")
    def test_get_writer_for_sync_engine(self, engine_mock):

        """
        Tests that driver uses Writer of sync engine
        """

        conf = config.ConnectionConfig(self.host, self.credentials)
        drvr = driver.AMQPDriver(conf)
        writer = drvr.get_writer()
        self.assertEqual(writer, engine_mock())

    def test_driver_uses_pika_async_engine(self):

        """
        Tests that driver uses async amqp engine if async_engine parameter=True
         in config object
        """
        conf = config.ConnectionConfig(self.host, self.credentials,
                                       async_engine=True)
        drvr = driver.AMQPDriver(conf)
        self.assertEqual(drvr._engine, pika_async)

    @mock.patch.object(pika_async, "Reader")
    def test_get_reader_for_async_engine(self, engine_mock):

        """
        Tests that driver uses Reader of async engine
        """

        conf = config.ConnectionConfig(self.host, self.credentials,
                                       async_engine=True)
        drvr = driver.AMQPDriver(conf)
        queue = "queue_name"
        preprocessor = mock.Mock()
        reader = drvr.get_reader(queue, preprocessor)
        self.assertEqual(reader, engine_mock())

    @mock.patch.object(pika_async, "Writer")
    def test_get_writer_for_async_engine(self, engine_mock):

        """
        Tests that driver uses Writer of async engine
        """

        conf = config.ConnectionConfig(self.host, self.credentials,
                                       async_engine=True)
        drvr = driver.AMQPDriver(conf)
        writer = drvr.get_writer()
        self.assertEqual(writer, engine_mock())


class AMQPDriverTestCase(unittest.TestCase):

    def setUp(self):
        super(AMQPDriverTestCase, self).setUp()
        self.user = "user"
        self.password = "password"
        self.credentials = config.Credentials(self.user, self.password)
        self.host = "host"
        self.conf = config.ConnectionConfig(self.host, self.credentials)
        self.driver = driver.AMQPDriver(self.conf)

    @mock.patch.object(driver.AMQPDriver, "_get_blocking_reader")
    def test_create_queue(self, get_blocking_reader_mock):

        """
        Tests that queue is created via blocking reader
        """

        queue = "queue_name"
        self.driver.create_queue(queue)
        get_blocking_reader_mock.assert_called_once_with(queue)
        get_blocking_reader_mock().create_queue.assert_called_once_with()

    @mock.patch.object(driver.AMQPDriver, "_get_blocking_writer")
    def test_create_exchange(self, get_blocking_writer_mock):

        """
        Tests that exchange is created via blocking writer
        """

        exchange_name = "exchange_name"
        self.driver.create_exchange(exchange_name)
        get_blocking_writer_mock.assert_called_once_with()
        get_blocking_writer_mock().create_exchange.assert_called_once_with(
            exchange_name, "topic")

    @mock.patch.object(driver.AMQPDriver, "_get_blocking_reader")
    def test_bind_queue(self, get_blocking_reader_mock):

        """
        Tests that queue is binded via blocking reader
        """

        queue = "queue_name"
        exchange = "exchange_name"
        service_name = "service_name"
        self.driver.bind_queue(queue, exchange, service_name)
        get_blocking_reader_mock.assert_called_once_with(queue)
        get_blocking_reader_mock().bind_queue.assert_called_once_with(
            exchange, service_name + ".#")

    def test_publish_message_via_existing_reader(self):

        """
        Tests that message is published via existing reader
        """
        self.driver._reader = mock.MagicMock()
        exchange = "exchange_name"
        routing_key = "rk"
        message = mock.MagicMock()
        self.driver.publish_message(exchange, routing_key, message)
        self.driver._reader.publish_message.assert_called_once_with(
            exchange, routing_key, message)

    @mock.patch.object(driver.AMQPDriver, "get_writer")
    def test_publish_message_via_new_writer(self, mock_get_writer):

        """
        Tests that message is published via existing reader
        """
        self.driver._reader = None
        exchange = "exchange_name"
        routing_key = "rk"
        message = mock.MagicMock()
        self.driver.publish_message(exchange, routing_key, message)
        mock_get_writer().publish_message.assert_called_once_with(
            exchange, routing_key, message)

    @mock.patch.object(driver.AMQPDriver, "get_reader")
    def test_listen_starts(self, mock_get_reader):

        """
        Tests that readers starts
        """
        self.driver._reader = None
        queue = "queue_name"
        preprocessor = mock.MagicMock()
        self.driver.listen(queue, preprocessor)
        mock_get_reader().run.assert_called_once_with()
        self.driver._reader = mock_get_reader()
