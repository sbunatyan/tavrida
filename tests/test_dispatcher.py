import unittest

import mock

from tavrida import dispatcher
from tavrida import messages
from tavrida import entry_point
from tavrida import exceptions
from tavrida import router
from tavrida import service


class DispatcherTestCase(unittest.TestCase):

    def setUp(self):
        super(DispatcherTestCase, self).setUp()
        self.dispatcher = dispatcher.Dispatcher()

    def test_handlers_dict(self):
        """
        Tests that _handlers dict contains correct sub-dicts
        """
        self.assertDictEqual(self.dispatcher.handlers,
                             {"request": {},
                              "response": {},
                              "error": {},
                              "notification": {}})

    def test_subscriptions_dict(self):
        """
        Tests that subscriptions dict is equal to 'notifications' dict
        """
        self.dispatcher._handlers["notification"] = {"some_key": "some_value"}
        self.assertDictEqual(self.dispatcher.subscriptions,
                             self.dispatcher._handlers["notification"])

    def test_register_duplicated_entry_point(self):
        """
        Tests registration duplicated entry point
        """
        ep = entry_point.EntryPoint("service", "method")
        message_type = "request"
        method_name = "method_name"
        self.dispatcher.register(ep, message_type, method_name)
        self.assertRaises(exceptions.DuplicatedEntryPointRegistration,
                          self.dispatcher.register, ep, message_type,
                          method_name)

    def test_register_duplicated_handler(self):
        """
        Tests registration duplicated entry point
        """
        ep1 = entry_point.EntryPoint("service1", "method1")
        ep2 = entry_point.EntryPoint("service2", "method2")
        message_type = "request"
        handler_method_name = "method_name"
        self.dispatcher.register(ep1, message_type, handler_method_name)
        self.assertRaises(exceptions.DuplicatedMethodRegistration,
                          self.dispatcher.register, ep2, message_type,
                          handler_method_name)

    def test_register_entry_point_handler_positive(self):
        """
        Tests successful handler registration for entry point
        """
        ep = entry_point.EntryPoint("service", "method")
        message_type = "request"
        method_name = "method_name"
        self.dispatcher.register(ep, message_type, method_name)
        self.assertEqual(self.dispatcher.handlers[message_type][str(ep)],
                         method_name)

    def test_get_handler_positive(self):
        """
        Tests get handler registered for ep
        """
        ep = entry_point.EntryPoint("service", "method")
        message_type = "request"
        method_name = "method_name"
        self.dispatcher.register(ep, message_type, method_name)
        self.assertEqual(self.dispatcher.get_handler(ep, message_type),
                         method_name)

    def test_get_handler_for_unknown_message_type(self):
        """
        Tests get handler for unknown message type
        """
        ep = entry_point.EntryPoint("service", "method")
        message_type = "zzz"
        self.assertRaises(exceptions.HandlerNotFound,
                          self.dispatcher.get_handler,
                          ep, message_type)

    def test_get_handler_for_unregistered_entry_point(self):
        """
        Tests get handler for unregistered entry point
        """
        ep = entry_point.EntryPoint("service", "method")
        message_type = "request"
        self.assertRaises(exceptions.HandlerNotFound,
                          self.dispatcher.get_handler,
                          ep, message_type)

    def test_get_publishers(self):
        """
        Tests entry points for publishers
        """
        ep = entry_point.EntryPoint("service", "method")
        message_type = "notification"
        method_name = "method_name"
        self.dispatcher.register(ep, message_type, method_name)
        res = list(self.dispatcher.get_publishers())
        self.assertListEqual(res, [ep])

    def test_get_request_entry_services(self):
        """
        Tests entry point's services for requests
        """
        ep = entry_point.EntryPoint("service", "method")
        message_type = "request"
        method_name = "method_name"
        self.dispatcher.register(ep, message_type, method_name)
        res = list(self.dispatcher.get_request_entry_services())
        self.assertListEqual(res, [ep.service])

    def test_get_dispatching_entry_point_for_request(self):
        """
        Tests request destination is used for dispatching
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        msg = messages.IncomingRequest(headers, context, payload)
        ep = self.dispatcher._get_dispatching_entry_point(msg)
        self.assertEqual(ep, msg.destination)

    def test_get_dispatching_entry_point_for_response(self):
        """
        Tests error source is used for dispatching
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        msg = messages.IncomingResponse(headers, context, payload)
        ep = self.dispatcher._get_dispatching_entry_point(msg)
        self.assertEqual(ep, msg.source)

    def test_get_dispatching_entry_point_for_error(self):
        """
        Tests error source is used for dispatching
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        msg = messages.IncomingError(headers, context, payload)
        ep = self.dispatcher._get_dispatching_entry_point(msg)
        self.assertEqual(ep, msg.source)

    def test_get_dispatching_entry_point_for_notification(self):
        """
        Tests notification source is used for dispatching
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        msg = messages.IncomingNotification(headers, context, payload)
        ep = self.dispatcher._get_dispatching_entry_point(msg)
        self.assertEqual(ep, msg.source)

    def test_get_source_context_for_request(self):
        """
        Tests request destination is used as source in proxy
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        msg = messages.IncomingRequest(headers, context, payload)
        ep = self.dispatcher._get_source_context(msg, service_instance)
        self.assertEqual(ep, msg.destination)

    def test_get_source_context_for_response(self):
        """
        Tests request destination is used as source in proxy
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        msg = messages.IncomingResponse(headers, context, payload)
        ep = self.dispatcher._get_source_context(msg, service_instance)
        self.assertEqual(ep, msg.destination)

    def test_get_source_context_for_error(self):
        """
        Tests request destination is used as source in proxy
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        msg = messages.IncomingResponse(headers, context, payload)
        ep = self.dispatcher._get_source_context(msg, service_instance)
        self.assertEqual(ep, msg.destination)

    def test_get_source_context_for_notification(self):
        """
        Tests request destination is used as source in proxy
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        service_instance.service_name = "service_name"
        msg = messages.IncomingNotification(headers, context, payload)
        ep = self.dispatcher._get_source_context(msg, service_instance)
        self.assertEqual(ep, entry_point.ServiceEntryPoint(
            service_instance.service_name))

    @mock.patch.object(dispatcher.Dispatcher, "_create_rpc_proxy")
    def test_process_request_by_service_instance(self, create_proxy_mock):
        """
        Tests that service instance processes message
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123",
            "message_type": "request"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        msg = messages.IncomingRequest(headers, context, payload)
        ep = entry_point.EntryPointFactory().create(msg.destination)
        message_type = "request"
        method_name = "some_handler"
        self.dispatcher.register(ep, message_type, method_name)
        res = self.dispatcher.process(msg, service_instance)
        service_instance.process.assert_called_once_with(method_name, msg,
                                                         create_proxy_mock())
        self.assertEqual(res, service_instance.process())

    @mock.patch.object(dispatcher.Dispatcher, "_create_rpc_proxy")
    def test_process_response_by_service_instance(self, create_proxy_mock):
        """
        Tests that service instance processes message
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123",
            "message_type": "response"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        msg = messages.IncomingResponse(headers, context, payload)
        ep = entry_point.EntryPointFactory().create(msg.source)
        message_type = "response"
        method_name = "some_handler"
        self.dispatcher.register(ep, message_type, method_name)
        res = self.dispatcher.process(msg, service_instance)
        service_instance.process.assert_called_once_with(method_name, msg,
                                                         create_proxy_mock())
        self.assertEqual(res, service_instance.process())

    @mock.patch.object(dispatcher.Dispatcher, "_create_rpc_proxy")
    def test_process_error_by_service_instance(self, create_proxy_mock):
        """
        Tests that service instance processes message
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123",
            "message_type": "error"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        msg = messages.IncomingError(headers, context, payload)
        ep = entry_point.EntryPointFactory().create(msg.source)
        message_type = "error"
        method_name = "some_handler"
        self.dispatcher.register(ep, message_type, method_name)
        res = self.dispatcher.process(msg, service_instance)
        service_instance.process.assert_called_once_with(method_name, msg,
                                                         create_proxy_mock())
        self.assertEqual(res, service_instance.process())

    @mock.patch.object(dispatcher.Dispatcher, "_create_rpc_proxy")
    def test_process_notification_by_service_instance(self, create_proxy_mock):
        """
        Tests that service instance processes message
        """
        headers = {
            "source": "src_service.src_method",
            "destination": "dst_service.dst_method",
            "reply_to": "rpl_service.rpl_method",
            "correlation_id": "123",
            "message_type": "notification"
        }
        context = {}
        payload = {}
        service_instance = mock.MagicMock()
        msg = messages.IncomingNotification(headers, context, payload)
        ep = entry_point.EntryPointFactory().create(msg.source)
        message_type = "notification"
        method_name = "some_handler"
        self.dispatcher.register(ep, message_type, method_name)
        res = self.dispatcher.process(msg, service_instance)
        service_instance.process.assert_called_once_with(method_name, msg,
                                                         create_proxy_mock())
        self.assertEqual(res, service_instance.process())


class RegisterRPCHandlerTestCase(unittest.TestCase):

    def tearDown(self):
        router.Router._services = []

    def test_register_handler_request(self):

        src = entry_point.EntryPointFactory().create("src_service.src_method")
        dst = entry_point.EntryPointFactory().create("dst_service.rpl_method")

        @dispatcher.rpc_service(dst.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.rpc_method(service=dst.service, method=dst.method)
            def handler(self):
                pass

        headers = {
            "source": str(src),
            "destination": str(dst),
            "reply_to": str(src),
            "correlation_id": "123",
            "message_type": "request"
        }
        context = {}
        payload = {}
        message = messages.IncomingRequest(headers, context, payload)
        service_cls = router.Router().get_rpc_service_cls(message)

        self.assertEqual(service_cls, SomeControllerClass)

        controller = SomeControllerClass(mock.MagicMock())
        disp = controller.get_dispatcher()
        handler = disp.get_handler(disp._get_dispatching_entry_point(message),
                                   "request")
        self.assertEqual("handler", handler)

    def test_register_handler_response(self):

        src = entry_point.EntryPointFactory().create("src_service.src_method")
        dst = entry_point.EntryPointFactory().create("dst_service.rpl_method")

        @dispatcher.rpc_service(dst.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.rpc_response_method(service=src.service,
                                            method=src.method)
            def handler(self):
                pass

        headers = {
            "source": str(src),
            "destination": str(dst),
            "reply_to": "",
            "correlation_id": "123",
            "message_type": "response"
        }
        context = {}
        payload = {}
        message = messages.IncomingResponse(headers, context, payload)
        service_cls = router.Router().get_rpc_service_cls(message)

        self.assertEqual(service_cls, SomeControllerClass)

        controller = SomeControllerClass(mock.MagicMock())
        disp = controller.get_dispatcher()
        handler = disp.get_handler(disp._get_dispatching_entry_point(message),
                                   "response")
        self.assertEqual("handler", handler)

    def test_register_handler_error(self):

        src = entry_point.EntryPointFactory().create("src_service.src_method")
        dst = entry_point.EntryPointFactory().create("dst_service.rpl_method")

        @dispatcher.rpc_service(dst.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.rpc_error_method(service=src.service,
                                         method=src.method)
            def handler(self):
                pass

        headers = {
            "source": str(src),
            "destination": str(dst),
            "reply_to": "",
            "correlation_id": "123",
            "message_type": "error"
        }
        context = {}
        payload = {}
        message = messages.IncomingError(headers, context, payload)
        service_cls = router.Router().get_rpc_service_cls(message)

        self.assertEqual(service_cls, SomeControllerClass)

        controller = SomeControllerClass(mock.MagicMock())
        disp = controller.get_dispatcher()
        handler = disp.get_handler(disp._get_dispatching_entry_point(message),
                                   "error")
        self.assertEqual("handler", handler)

    def test_register_handler_subscription(self):

        src = entry_point.EntryPointFactory().create("src_service.src_method")
        dst = entry_point.EntryPointFactory().create("dst_service.rpl_method")

        @dispatcher.rpc_service(dst.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.subscription_method(service=src.service,
                                            method=src.method)
            def handler(self):
                pass

        headers = {
            "source": str(src),
            "destination": "",
            "reply_to": "",
            "correlation_id": "123",
            "message_type": "notification"
        }
        context = {}
        payload = {}
        message = messages.IncomingNotification(headers, context, payload)
        service_classes = router.Router().get_subscription_cls(message)

        self.assertEqual(service_classes, [SomeControllerClass])

        controller = SomeControllerClass(mock.MagicMock())
        disp = controller.get_dispatcher()
        handler = controller.get_dispatcher().get_handler(
            disp._get_dispatching_entry_point(message), "notification")
        self.assertEqual("handler", handler)
