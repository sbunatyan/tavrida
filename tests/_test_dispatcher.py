import unittest

import mock

from tavrida import dispatcher
from tavrida import exceptions
from tavrida import messages
from tavrida import router
from tavrida import service


class TestDispatcherRegisterTestCase(unittest.TestCase):

    def setUp(self):
        super(TestDispatcherRegisterTestCase, self).setUp()
        self.dispatcher = dispatcher.Dispatcher()

    def test_register_request_handler(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "request"
        method_name = "handler_method"

        self.dispatcher.register(ep, message_type, method_name)
        self.assertEqual(self.dispatcher.handlers[message_type][ep.method],
                         method_name)

    def test_register_response_handler(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "response"
        method_name = "handler_method"

        self.dispatcher.register(ep, message_type, method_name)
        self.assertEqual(self.dispatcher.handlers[message_type][ep.method],
                         method_name)

    def test_register_error_handler(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "error"
        method_name = "handler_method"

        self.dispatcher.register(ep, message_type, method_name)
        self.assertEqual(self.dispatcher.handlers[message_type][ep.method],
                         method_name)

    def test_duplicated_entry_point(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "request"
        method_name = "handler_method"
        self.dispatcher._handlers[message_type][ep.method] = mock.MagicMock()
        self.assertRaises(exceptions.DuplicatedEntryPointRegistration,
                          self.dispatcher.register, ep, message_type,
                          method_name)

    def test_duplicated_method(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "request"
        method_name = "handler_method"
        self.dispatcher._handlers[message_type]["other_ep"] = method_name
        self.assertRaises(exceptions.DuplicatedMethodRegistration,
                          self.dispatcher.register, ep, message_type,
                          method_name)


class DispatcherGetHandlerTestCase(unittest.TestCase):

    def setUp(self):
        super(DispatcherGetHandlerTestCase, self).setUp()
        self.dispatcher = dispatcher.Dispatcher()

    def test_get_handler_positive(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "request"
        handler_method = mock.MagicMock()
        self.dispatcher._handlers[message_type][ep.method] = handler_method
        res = self.dispatcher.get_handler(ep, message_type)
        self.assertEqual(res, handler_method)

    def test_get_handler_for_wrong_message_type(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "wrong_type"
        self.assertRaises(exceptions.HandlerNotFound,
                          self.dispatcher.get_handler, ep, message_type)

    def test_get_handler_for_wrongep_method(self):
        ep = mock.MagicMock()
        ep.method = "ep_method"
        message_type = "request"
        handler_method = mock.MagicMock()
        self.dispatcher._handlers[message_type]["some_method"] = handler_method
        self.assertRaises(exceptions.HandlerNotFound,
                          self.dispatcher.get_handler, ep, message_type)


class DispatcherGetEPTestCase(unittest.TestCase):

    def setUp(self):
        super(DispatcherGetEPTestCase, self).setUp()
        self.dispatcher = dispatcher.Dispatcher()

    def test_get_dispatching_entry_point_for_error(self):
        message = mock.MagicMock()
        message.__class__ = messages.IncomingError
        res = self.dispatcher._get_dispatching_entry_point(message)
        self.assertEqual(res, message.source)

    def test_get_dispatching_entry_point_for_response(self):
        message = mock.MagicMock()
        message.__class__ = messages.IncomingResponse
        res = self.dispatcher._get_dispatching_entry_point(message)
        self.assertEqual(res, message.source)

    def test_get_dispatching_entry_point_for_request(self):
        message = mock.MagicMock()
        message.__class__ = messages.IncomingRequest
        res = self.dispatcher._get_dispatching_entry_point(message)
        self.assertEqual(res, message.destination)


class DispatcherProcessTestCase(unittest.TestCase):

    def setUp(self):
        super(DispatcherProcessTestCase, self).setUp()
        self.dispatcher = dispatcher.Dispatcher()

    @mock.patch.object(dispatcher.Dispatcher, "_create_rpc_proxy")
    def test_process(self, create_proxy_mock):
        ep = mock.MagicMock()
        ep.service = "ep_service"
        ep.method = "ep_method"
        message_type = "request"
        method_name = "handler_method"
        self.dispatcher.register(ep, message_type, method_name)

        message = mock.MagicMock()
        message.message_type = message_type
        message.type = message_type
        message.destination = ep
        service_instance = mock.MagicMock()
        res = self.dispatcher.process(message, service_instance)
        service_instance.process.assert_called_once_with(method_name,
                                                         message,
                                                         create_proxy_mock())
        self.assertEqual(res, service_instance.process())


class RegisterRPCHandlerTestCase(unittest.TestCase):

    def tearDown(self):
        router.Router._services = {}
        router.Router._subscriptions = {}

    def test_register_handler_request(self):

        ep = mock.MagicMock()
        ep.service = "ep_service"
        ep.method = "ep_method"

        @dispatcher.rpc_service(ep.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.rpc_method(service=ep.service, method=ep.method)
            def handler(self):
                pass

        message_type = "request"
        message = mock.MagicMock()
        message.message_type = message_type
        message.type = message_type
        message.destination = ep
        service_cls = router.Router()._get_service_cls(message.destination)

        self.assertEqual(service_cls, SomeControllerClass)

        controller = SomeControllerClass(mock.MagicMock(), mock.MagicMock())
        handler = controller.get_dispatcher().get_handler(ep, message_type)
        self.assertEqual("handler", handler)

    def test_register_handler_response(self):

        ep = mock.MagicMock()
        ep.service = "ep_service"
        ep.method = "ep_method"

        @dispatcher.rpc_service(ep.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.rpc_response_method(service=ep.service,
                                            method=ep.method)
            def handler(self):
                pass

        message_type = "response"
        message = mock.MagicMock()
        message.message_type = message_type
        message.type = message_type
        message.destination = ep
        service_cls = router.Router()._get_service_cls(message.destination)

        self.assertEqual(service_cls, SomeControllerClass)

        controller = SomeControllerClass(mock.MagicMock(), mock.MagicMock())
        handler = controller.get_dispatcher().get_handler(ep, message_type)
        self.assertEqual("handler", handler)

    def test_register_handler_error(self):

        ep = mock.MagicMock()
        ep.service = "ep_service"
        ep.method = "ep_method"

        @dispatcher.rpc_service(ep.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.rpc_error_method(service=ep.service, method=ep.method)
            def handler(self):
                pass

        message_type = "error"
        message = mock.MagicMock()
        message.message_type = message_type
        message.type = message_type
        message.destination = ep
        service_cls = router.Router()._get_service_cls(message.destination)

        self.assertEqual(service_cls, SomeControllerClass)

        controller = SomeControllerClass(mock.MagicMock(), mock.MagicMock())
        handler = controller.get_dispatcher().get_handler(ep, message_type)
        self.assertEqual("handler", handler)

    def test_register_handler_subscription(self):

        ep = mock.MagicMock()
        ep.service = "ep_service"
        ep.method = "ep_method"

        @dispatcher.rpc_service(ep.service)
        class SomeControllerClass(service.ServiceController):
            @dispatcher.subscription_method(service=ep.service,
                                            method=ep.method)
            def handler(self):
                pass

        message_type = "notification"
        message = mock.MagicMock()
        message.message_type = message_type
        message.type = message_type
        message.source = ep
        service_cls = router.Router()._get_service_cls(message.source)

        self.assertEqual(service_cls, SomeControllerClass)

        controller = SomeControllerClass(mock.MagicMock(), mock.MagicMock())
        handler = controller.get_subscription().get_handler(ep)
        self.assertEqual("handler", handler)
