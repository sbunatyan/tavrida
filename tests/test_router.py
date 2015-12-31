import unittest

import mock

from tavrida import exceptions
from tavrida import messages
from tavrida import router
from tavrida import service


class RouterTestCase(unittest.TestCase):

    def setUp(self):
        super(RouterTestCase, self).setUp()
        self.router = router.Router()

    def tearDown(self):
        super(RouterTestCase, self).tearDown()
        self.router._services = []

    def test_router_is_singleton(self):
        """
        Tests router is singleton
        """
        router2 = router.Router()
        self.assertEqual(self.router, router2)

    def test_register_service_class_first_time(self):
        """
        Test first service class registration attempt for service name
        """
        service_name = "service_name"
        service_cls = mock.MagicMock()
        self.router.register(service_name, service_cls)
        self.assertListEqual(self.router.services,
                             [{service_name: service_cls}])

    def test_register_service_class_second_time(self):
        """
        Test second service class registration attempt for service name
        """
        service_name = "service_name"
        service_cls = mock.MagicMock()
        self.router.register(service_name, service_cls)
        self.router.register(service_name, service_cls)
        self.assertListEqual(self.router.services,
                             [{service_name: service_cls}])

    def test_request_destination_not_in_rpc_mapping(self):
        """
        Test if request destination is not in rpc mapping
        """
        msg = mock.MagicMock()
        rpc_mapping = {}
        self.assertFalse(self.router._check_if_request_suits(
            msg, rpc_mapping))

    def test_request_destination_in_rpc_mapping(self):
        """
        Tests request destination is in rpc mapping
        """
        msg = mock.MagicMock()
        rpc_mapping = {msg.destination.service: mock.MagicMock()}
        self.assertTrue(self.router._check_if_request_suits(msg,
                                                            rpc_mapping))

    def test_response_source_is_not_in_rpc_mapping(self):
        """
        Tests response source service isn't equal to service controller service
        name
        """
        msg = mock.MagicMock()
        rpc_mapping = {}
        self.assertFalse(self.router._check_if_response_suits(msg,
                                                              rpc_mapping))

    def test_response_destination_not_equal_to_controller_service_name(self):
        """
        Tests response source service is not equal to service controller
        service name
        """
        msg = mock.MagicMock()
        rpc_mapping = {}
        service_cls = mock.MagicMock()
        rpc_mapping[msg.source.service] = service_cls
        self.assertFalse(self.router._check_if_response_suits(msg,
                                                              rpc_mapping))

    def test_response_destination_equal_to_controller_service_name(self):
        """
        Tests response source service is equal to service controller
        service name
        """
        msg = mock.MagicMock()
        rpc_mapping = {}
        service_cls = mock.MagicMock()
        service_cls.service_name = msg.destination.service
        rpc_mapping[msg.source.service] = service_cls
        self.assertTrue(self.router._check_if_response_suits(msg, rpc_mapping))

    @mock.patch.object(router.Router, "_check_if_response_suits")
    def test_rpc_service_not_found_for_response(self, check_response):
        """
        Tests RPC service controller class is not found for response
        """
        check_response.return_value = False
        message = mock.MagicMock(spec=messages.IncomingResponse)
        message.source = mock.MagicMock()
        self.assertRaises(exceptions.ServiceNotFound,
                          self.router.get_rpc_service_cls,
                          message)

    @mock.patch.object(router.Router, "_check_if_response_suits")
    def test_rpc_service_not_found_for_error(self, check_response):
        """
        Tests RPC service controller class is not found for error
        """
        check_response.return_value = False
        message = mock.MagicMock(spec=messages.IncomingError)
        message.source = mock.MagicMock()
        self.assertRaises(exceptions.ServiceNotFound,
                          self.router.get_rpc_service_cls,
                          message)

    @mock.patch.object(router.Router, "_check_if_request_suits")
    def test_rpc_service_not_found_for_request(self, check_request):
        """
        Tests RPC service controller class is not found for request
        """
        check_request.return_value = False
        message = mock.MagicMock(spec=messages.IncomingRequest)
        message.destination = mock.MagicMock()
        self.assertRaises(exceptions.ServiceNotFound,
                          self.router.get_rpc_service_cls,
                          message)

    @mock.patch.object(router.Router, "_check_if_response_suits")
    def test_rpc_duplicated_registration_for_response(self, check_response):
        """
        Tests RPC service controller is registered multiple times for response
        """
        check_response.return_value = True
        message = mock.MagicMock(spec=messages.IncomingResponse)
        message.source = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        service_cls2 = mock.MagicMock()
        self.router.register(message.source.service, service_cls1)
        self.router.register(message.source.service, service_cls2)
        self.assertRaises(exceptions.DuplicatedServiceRegistration,
                          self.router.get_rpc_service_cls,
                          message)

    @mock.patch.object(router.Router, "_check_if_response_suits")
    def test_rpc_service_not_found_for_error(self, check_response):
        """
        Tests RPC service controller is registered multiple times for error
        """
        check_response.return_value = True
        message = mock.MagicMock(spec=messages.IncomingError)
        message.source = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        service_cls2 = mock.MagicMock()
        self.router.register(message.source.service, service_cls1)
        self.router.register(message.source.service, service_cls2)
        self.assertRaises(exceptions.DuplicatedServiceRegistration,
                          self.router.get_rpc_service_cls,
                          message)

    @mock.patch.object(router.Router, "_check_if_request_suits")
    def test_rpc_service_not_found_for_request(self, check_request):
        """
        Tests RPC service controller is registered multiple times for request
        """
        check_request.return_value = True
        message = mock.MagicMock(spec=messages.IncomingRequest)
        message.destination = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        service_cls2 = mock.MagicMock()
        self.router.register(message.destination.service, service_cls1)
        self.router.register(message.destination.service, service_cls2)
        self.assertRaises(exceptions.DuplicatedServiceRegistration,
                          self.router.get_rpc_service_cls,
                          message)

    @mock.patch.object(router.Router, "_check_if_response_suits")
    def test_get_rpc_service_cls_for_response(self, check_response):
        """
        Tests RPC service controller is registered multiple times for response
        """
        check_response.return_value = True
        message = mock.MagicMock(spec=messages.IncomingResponse)
        message.source = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        self.router.register(message.source.service, service_cls1)
        self.assertEqual(self.router.get_rpc_service_cls(message),
                         service_cls1)

    @mock.patch.object(router.Router, "_check_if_response_suits")
    def test_get_rpc_service_cls_for_error(self, check_response):
        """
        Tests RPC service controller is registered multiple times for error
        """
        check_response.return_value = True
        message = mock.MagicMock(spec=messages.IncomingError)
        message.source = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        self.router.register(message.source.service, service_cls1)
        self.assertEqual(self.router.get_rpc_service_cls(message),
                         service_cls1)

    @mock.patch.object(router.Router, "_check_if_request_suits")
    def test_get_rpc_service_cls_for_request(self, check_request):
        """
        Tests RPC service controller is registered multiple times for error
        """
        check_request.return_value = True
        message = mock.MagicMock(spec=messages.IncomingRequest)
        message.destination = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        self.router.register(message.destination.service, service_cls1)
        self.assertEqual(self.router.get_rpc_service_cls(message),
                         service_cls1)

    def test_get_one_subscription_cls_for_service(self):
        """
        Tests getting one subscription service class for remote service
        """
        message = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        self.router.register(message.source.service, service_cls1)
        self.assertListEqual(self.router.get_subscription_cls(message),
                             [service_cls1])

    def test_get_multiple_subscription_cls_for_service(self):
        """
        Tests getting multiple subscription service class for remote service
        """
        message = mock.MagicMock()
        service_cls1 = mock.MagicMock()
        service_cls2 = mock.MagicMock()
        self.router.register(message.source.service, service_cls1)
        self.router.register(message.source.service, service_cls2)
        self.assertListEqual(self.router.get_subscription_cls(message),
                             [service_cls1, service_cls2])

    def test_get_service(self):
        """
        Tests getting service object of given class from list of services
        """
        class A(object):
            pass

        class B(object):
            pass

        service_1 = A()
        service_2 = B()
        service_list = [service_1, service_2]
        self.assertEqual(self.router._get_service(A, service_list),
                         service_1)

    def test_get_unknown_service(self):
        """
        Tests getting service object of wrong class from list of services
        """
        class A(object):
            pass

        class B(object):
            pass

        service_list = [A()]
        self.assertRaises(exceptions.UnknownService,
                          self.router._get_service, B, service_list)

    def test_reverse_lookup(self):
        """
        Tests lookup service name by service class
        """
        service_name = "service_name"
        service_cls = mock.MagicMock()
        self.router.register(service_name, service_cls)
        res = list(self.router.reverse_lookup(service_cls))
        self.assertListEqual(res, [service_name])

    def test_reverse_lookup_unregistered_service(self):
        """
        Tests failed lookup service name by service class
        """
        service_cls = mock.MagicMock()
        res = self.router.reverse_lookup(service_cls)
        self.assertRaises(exceptions.ServiceIsNotRegister,
                          list, res)

    def test_process_rpc(self):
        """
        Tests that correct class is passed to dispatcher
        """
        class A(service.ServiceController):
            get_dispatcher = mock.MagicMock()

        postprocessor = mock.MagicMock()
        message, service_cls = mock.MagicMock(), A
        service_instance = service_cls(postprocessor)
        service_list = [service_instance]
        service_name = "service_name"
        self.router.register(service_name, service_cls)
        self.router._process_rpc(message, service_cls, service_list)
        service_cls.get_dispatcher().process.assert_called_once_with(
            message,  service_instance)

    def test_process_subscription(self):
        """
        Tests that correct class is passed to dispatcher for each subscription
        """
        class A(service.ServiceController):
            get_dispatcher = mock.MagicMock()

        postprocessor = mock.MagicMock()
        message, service_classes = mock.MagicMock(), [A]
        service_instance = A(postprocessor)
        service_list = [service_instance]
        service_name = "service_name"
        self.router.register(service_name, A)
        self.router._process_subscription(message, service_classes,
                                          service_list)
        A.get_dispatcher().process.assert_called_once_with(
            message,  service_instance)

    @mock.patch.object(router.Router, "get_subscription_cls")
    @mock.patch.object(router.Router, "_process_subscription")
    def test_process_notification(self, process_mock, get_cls_mock):
        """
        Tests notification correctly processed to method _process_subscription
        """
        message = mock.MagicMock(spec=messages.IncomingNotification)
        service_list = [mock.MagicMock()]
        self.router.process(message, service_list)
        process_mock.assert_called_once_with(message, get_cls_mock(),
                                             service_list)

    @mock.patch.object(router.Router, "get_rpc_service_cls")
    @mock.patch.object(router.Router, "_process_rpc")
    def test_process_request(self, process_mock, get_cls_mock):
        """
        Tests request correctly processed to method _process_rpc
        """
        message = mock.MagicMock(spec=messages.IncomingRequest)
        service_list = [mock.MagicMock()]
        self.router.process(message, service_list)
        process_mock.assert_called_once_with(message, get_cls_mock(),
                                             service_list)

    @mock.patch.object(router.Router, "get_rpc_service_cls")
    @mock.patch.object(router.Router, "_process_rpc")
    def test_process_response(self, process_mock, get_cls_mock):
        """
        Tests response correctly processed to method _process_rpc
        """
        message = mock.MagicMock(spec=messages.IncomingResponse)
        service_list = [mock.MagicMock()]
        self.router.process(message, service_list)
        process_mock.assert_called_once_with(message, get_cls_mock(),
                                             service_list)

    @mock.patch.object(router.Router, "get_rpc_service_cls")
    @mock.patch.object(router.Router, "_process_rpc")
    def test_process_error(self, process_mock, get_cls_mock):
        """
        Tests error correctly processed to method _process_rpc
        """
        message = mock.MagicMock(spec=messages.IncomingError)
        service_list = [mock.MagicMock()]
        self.router.process(message, service_list)
        process_mock.assert_called_once_with(message, get_cls_mock(),
                                             service_list)
