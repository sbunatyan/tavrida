import copy
import unittest

import mock

from tavrida import exceptions
from tavrida import messages
from tavrida import service


class ServiceTestCase(unittest.TestCase):

    def setUp(self):
        super(ServiceTestCase, self).setUp()
        self.postprocessor = mock.MagicMock()
        self.service = service.ServiceController(self.postprocessor)

    def test_only_one_dispatcher_for_service(self):
        """
        Tests that service has only one dispatcher
        """
        disp1 = self.service.get_dispatcher()
        disp2 = self.service.get_dispatcher()
        self.assertEqual(disp1, disp2)

    def test_set_dispatcher(self):
        """
        Tests discovery setting for service
        """
        disc = mock.MagicMock()
        self.service.set_discovery(disc)
        self.assertEqual(disc, self.service._discovery)

    def test_get_dispatcher(self):
        """
        Tests discovery getting for service
        """
        disc = mock.MagicMock()
        self.service.set_discovery(disc)
        self.assertEqual(disc, self.service.get_discovery())

    def test_add_incoming_middleware(self):
        """
        Tests incoming middleware addition to service
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        self.assertListEqual(self.service._incoming_middlewares, [middleware])

    def test_add_outgoing_middleware(self):
        """
        Tests outgoing middleware addition to service
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        self.assertListEqual(self.service._incoming_middlewares, [middleware])

    def test_run_outgoing_middlewares(self):
        """
        Tests outgoing middlewares are run
        """
        middleware = mock.MagicMock()
        result = mock.MagicMock()
        self.service.add_outgoing_middleware(middleware)
        res = self.service._run_outgoing_middlewares(result)
        middleware.process.assert_called_once_with(result)
        self.assertEqual(res, middleware.process())

    def test_send(self):
        """
        Tests that massage is sent by postprocessor
        """
        message = mock.MagicMock()
        res = self.service._send(message)
        self.postprocessor.process.assert_called_once_with(message)
        self.assertEqual(res, self.postprocessor.process())

    def test_filter_lack_of_parameters(self):
        """
        Tests if number of incoming parameters less that method accepts
        """
        self.service.method = lambda x: x
        self.service.method._arg_names = ["request", "proxy", "x"]
        self.assertRaises(ValueError,
                          self.service._filter_redundant_parameters,
                          "method", {})

    def test_filter_no_required_parameters(self):
        """
        Tests if some of method parameters are not present
        """
        self.service.method = lambda x: x
        self.service.method._arg_names = ["request", "proxy", "x"]
        self.assertRaises(ValueError,
                          self.service._filter_redundant_parameters,
                          "method", {"y": "y"})

    def test_filter_redundant_parameters(self):
        """
        Tests filtering redundant parameters
        """
        self.service.method = lambda x: x
        self.service.method._arg_names = ["request", "proxy", "x"]
        res = self.service._filter_redundant_parameters("method", {"y": "y",
                                                                   "x": "x"})
        self.assertDictEqual(res, {"x": "x"})

    def test_filter_no_redundant_parameters(self):
        """
        Tests filtering redundant parameters when no there are no redundant
        parameters
        """
        self.service.method = lambda x: x
        self.service.method._arg_names = ["request", "proxy", "x"]
        res = self.service._filter_redundant_parameters("method", {"x": "x"})
        self.assertDictEqual(res, {"x": "x"})

    @mock.patch.object(service.ServiceController,
                       "_filter_redundant_parameters")
    def test_handle_request_call_positive(self, filter_mock):
        """
        Tests successful request (IncomingRequestCall) handling
        """
        self.service.method = mock.MagicMock()
        method = "method"
        request = mock.MagicMock(spec=messages.IncomingRequestCall)
        request.payload = {"param": "value"}
        filter_mock.return_value = request.payload
        proxy = mock.MagicMock()
        res = self.service._handle_request(method, request, proxy)
        self.service.method.assert_called_once_with(request, proxy,
                                                    **filter_mock())
        self.assertEqual(res, self.service.method())

    @mock.patch.object(service.ServiceController,
                       "_filter_redundant_parameters")
    def test_handle_request_cast_positive(self, filter_mock):
        """
        Tests successful request (IncomingRequestCast) handling
        """
        self.service.method = mock.MagicMock()
        method = "method"
        request = mock.MagicMock(spec=messages.IncomingRequestCast)
        request.payload = {"param": "value"}
        filter_mock.return_value = request.payload
        proxy = mock.MagicMock()
        res = self.service._handle_request(method, request, proxy)
        self.service.method.assert_called_once_with(request, proxy,
                                                    **filter_mock())
        self.assertIsNone(res)

    @mock.patch.object(service.ServiceController,
                       "_filter_redundant_parameters")
    def test_handle_request_call_with_non_aclable_exception(self, filter_mock):
        """
        Tests request (IncomingRequestCall) handling when non-ackable
        exception raises
        """
        self.service.method = mock.MagicMock(side_effect=Exception)
        method = "method"
        request = mock.MagicMock(spec=messages.IncomingRequestCall)
        request.payload = {"param": "value"}
        request.correlation_id = "123"
        request.request_id = "456"
        request.destination = mock.MagicMock()
        request.reply_to = mock.MagicMock()
        request.source = mock.MagicMock()
        proxy = mock.MagicMock()
        filter_mock.return_value = request.payload
        res = self.service._handle_request(method, request, proxy)
        self.service.method.assert_called_once_with(request, proxy,
                                                    **filter_mock())
        self.assertIsInstance(res, messages.Error)
        self.assertEqual(res.payload["class"],
                         exceptions.BaseException.__name__)

    @mock.patch.object(service.ServiceController,
                       "_filter_redundant_parameters")
    def test_handle_request_call_with_ackable_exception(self, filter_mock):
        """
        Tests request (IncomingRequestCall) handling when ackable
        exception raises
        """
        self.service.method = mock.MagicMock(
            side_effect=exceptions.BaseAckableException)
        method = "method"
        request = mock.MagicMock(spec=messages.IncomingRequestCall)
        request.payload = {"param": "value"}
        request.correlation_id = "123"
        request.request_id = "456"
        request.destination = mock.MagicMock()
        request.reply_to = mock.MagicMock()
        request.source = mock.MagicMock()
        proxy = mock.MagicMock()
        filter_mock.return_value = request.payload
        res = self.service._handle_request(method, request, proxy)
        self.service.method.assert_called_once_with(request, proxy,
                                                    **filter_mock())
        self.assertIsInstance(res, messages.Error)
        self.assertEqual(res.payload["class"],
                         exceptions.BaseAckableException.__name__)

    @mock.patch.object(service.ServiceController, "_handle_request")
    @mock.patch.object(service.ServiceController, "_run_outgoing_middlewares")
    @mock.patch.object(service.ServiceController, "_send")
    def test_process_request_and_send_response(self,
                                               send_nock,
                                               run_out_middlewares_mock,
                                               handle_mock):
        """
        Tests successful request processing and the response sending
        """
        res = mock.MagicMock(spec=messages.Response)
        handle_mock.return_value = res
        method = "method"
        request = mock.MagicMock()
        proxy = mock.MagicMock()
        self.service._process_request(method, request, proxy)
        handle_mock.assert_called_once_with(method, request, proxy)
        run_out_middlewares_mock.assert_called_once_with(handle_mock())
        send_nock.assert_called_once_with(run_out_middlewares_mock())

    @mock.patch.object(service.ServiceController, "_handle_request")
    @mock.patch.object(service.ServiceController, "_run_outgoing_middlewares")
    @mock.patch.object(service.ServiceController, "_send")
    def test_process_request_and_send_error(self,
                                            send_nock,
                                            run_out_middlewares_mock,
                                            handle_mock):
        """
        Tests request processing and the error sending
        """
        res = mock.MagicMock(spec=messages.Error)
        handle_mock.return_value = res
        method = "method"
        request = mock.MagicMock()
        proxy = mock.MagicMock()
        self.service._process_request(method, request, proxy)
        handle_mock.assert_called_once_with(method, request, proxy)
        run_out_middlewares_mock.assert_called_once_with(handle_mock())
        send_nock.assert_called_once_with(run_out_middlewares_mock())

    @mock.patch.object(service.ServiceController, "_handle_request")
    @mock.patch.object(service.ServiceController, "_run_outgoing_middlewares")
    @mock.patch.object(service.ServiceController, "_send")
    def test_process_request_and_handle_dict_response(self,
                                                      send_nock,
                                                      run_out_middlewares_mock,
                                                      handle_mock):
        """
        Tests request processing and response dict sending
        """
        handle_mock.return_value = {"aaa": "bbb"}
        method = "method"
        request = mock.MagicMock()
        proxy = mock.MagicMock()
        self.service._process_request(method, request, proxy)
        handle_mock.assert_called_once_with(method, request, proxy)
        run_out_middlewares_mock.assert_called_once_with(
            request.make_response())
        send_nock.assert_called_once_with(run_out_middlewares_mock())

    @mock.patch.object(service.ServiceController, "_handle_request")
    def test_process_request_with_incorrect_response(self, handle_mock):
        """
        Tests request processing with incorrect response type
        """
        res = True
        handle_mock.return_value = res
        method = "method"
        request = mock.MagicMock()
        proxy = mock.MagicMock()
        self.assertRaises(exceptions.WrongResponse,
                          self.service._process_request,
                          method, request, proxy)

    @mock.patch.object(copy, "copy")
    @mock.patch.object(service.ServiceController, "_process_request")
    def test_route_request_call(self, process_mock, copy_mock):
        """
        Tests routing request call to corresponding handler
        """
        message = mock.MagicMock(spec=messages.IncomingRequestCall)
        message.update_context = mock.MagicMock()
        message.payload = mock.MagicMock()
        method = "method"
        proxy = mock.MagicMock()

        res = self.service._route_message_by_type(method, message, proxy)
        copy_mock.assert_called_once_with(message.payload)
        message.update_context.assert_called_once_with(copy_mock())
        self.assertEqual(res, process_mock())

    @mock.patch.object(copy, "copy")
    @mock.patch.object(service.ServiceController, "_process_request")
    def test_route_request_cast(self, process_mock, copy_mock):
        """
        Tests routing request cast to corresponding handler
        """
        message = mock.MagicMock(spec=messages.IncomingRequestCast)
        message.update_context = mock.MagicMock()
        message.payload = mock.MagicMock()
        method = "method"
        proxy = mock.MagicMock()

        res = self.service._route_message_by_type(method, message, proxy)
        copy_mock.assert_called_once_with(message.payload)
        message.update_context.assert_called_once_with(copy_mock())
        self.assertEqual(res, process_mock())

    @mock.patch.object(copy, "copy")
    @mock.patch.object(service.ServiceController, "_process_response")
    def test_route_response(self, process_mock, copy_mock):
        """
        Tests routing response to corresponding handler
        """
        message = mock.MagicMock(spec=messages.IncomingResponse)
        message.update_context = mock.MagicMock()
        message.payload = mock.MagicMock()
        method = "method"
        proxy = mock.MagicMock()

        res = self.service._route_message_by_type(method, message, proxy)
        copy_mock.assert_called_once_with(message.payload)
        message.update_context.assert_called_once_with(copy_mock())
        self.assertEqual(res, process_mock())

    @mock.patch.object(copy, "copy")
    @mock.patch.object(service.ServiceController, "_process_notification")
    def test_route_notification(self, process_mock, copy_mock):
        """
        Tests routing notification to corresponding handler
        """
        message = mock.MagicMock(spec=messages.IncomingNotification)
        message.update_context = mock.MagicMock()
        message.payload = mock.MagicMock()
        method = "method"
        proxy = mock.MagicMock()

        res = self.service._route_message_by_type(method, message, proxy)
        copy_mock.assert_called_once_with(message.payload)
        message.update_context.assert_called_once_with(copy_mock())
        self.assertEqual(res, process_mock())

    @mock.patch.object(copy, "copy")
    @mock.patch.object(service.ServiceController, "_process_error")
    def test_route_error(self, process_mock, copy_mock):
        """
        Tests routing error to corresponding handler
        """
        message = mock.MagicMock(spec=messages.IncomingError)
        message.update_context = mock.MagicMock()
        message.payload = mock.MagicMock()
        method = "method"
        proxy = mock.MagicMock()

        res = self.service._route_message_by_type(method, message, proxy)
        copy_mock.assert_called_once_with(message.payload)
        message.update_context.assert_called_once_with(copy_mock())
        self.assertEqual(res, process_mock())

    @mock.patch.object(service.ServiceController, "_send")
    def test_incoming_middlewares_for_request_and_response(self, send_mock):
        """
        Tests run middlewares for request and sending the response
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        res = mock.MagicMock(spec=messages.Response)
        middleware.process = mock.MagicMock(return_value=res)

        message = mock.MagicMock(spec=messages.IncomingRequestCall)
        result = self.service._run_incoming_middlewares(message)
        middleware.process.assert_called_once_with(message)
        send_mock.assert_called_once_with(middleware.process())
        self.assertTupleEqual(result, (False, res))

    @mock.patch.object(service.ServiceController, "_send")
    def test_incoming_middlewares_for_request_and_error(self, send_mock):
        """
        Tests run middlewares for request and sending the error
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        res = mock.MagicMock(spec=messages.Error)
        middleware.process = mock.MagicMock(return_value=res)

        message = mock.MagicMock(spec=messages.IncomingRequestCall)
        result = self.service._run_incoming_middlewares(message)
        middleware.process.assert_called_once_with(message)
        send_mock.assert_called_once_with(middleware.process())
        self.assertTupleEqual(result, (False, res))

    def test_incoming_middlewares_for_request_cast(self):
        """
        Tests run middlewares for request cast without response
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        res = mock.MagicMock(spec=list)
        middleware.process = mock.MagicMock(return_value=res)

        message = mock.MagicMock(spec=messages.IncomingRequestCast)
        result = self.service._run_incoming_middlewares(message)
        middleware.process.assert_called_once_with(message)
        self.assertTupleEqual(result, (True, res))

    def test_incoming_middlewares_for_request_cast_with_stop_processing(self):
        """
        Tests run middlewares for request cast without response
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        res = mock.MagicMock(spec=messages.Response)
        middleware.process = mock.MagicMock(return_value=res)

        message = mock.MagicMock(spec=messages.IncomingRequestCast)
        result = self.service._run_incoming_middlewares(message)
        middleware.process.assert_called_once_with(message)
        self.assertTupleEqual(result, (False, res))

    @mock.patch.object(service.ServiceController, "_route_message_by_type")
    def test_process_message_with_middleware_interruption(self, route_mock):
        """
        Tests run middlewares for request with response from middleware
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        res = mock.MagicMock(spec=messages.IncomingRequestCall)
        middleware.process = mock.MagicMock(return_value=res)

        message = mock.MagicMock(spec=messages.IncomingRequestCall)
        method = "method"
        proxy = mock.MagicMock()

        self.service.process(method, message, proxy)
        route_mock.assert_called_once_with(method, res, proxy)

    @mock.patch.object(service.ServiceController, "_route_message_by_type")
    def test_process_request_cast_with_middleware_stop_processing(self,
                                                                  route_mock):
        """
        Tests run middlewares for request with middleware processing stop
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        res = mock.MagicMock(spec=messages.Response)
        middleware.process = mock.MagicMock(return_value=res)

        message = mock.MagicMock(spec=messages.IncomingRequestCast)
        method = "method"
        proxy = mock.MagicMock()

        self.service.process(method, message, proxy)
        route_mock.assert_not_called()

    @mock.patch.object(service.ServiceController, "_route_message_by_type")
    @mock.patch.object(service.ServiceController, "_send")
    def test_process_request_call_with_middleware_stop_processing(self,
                                                                  send_mock,
                                                                  route_mock):
        """
        Tests run middlewares for request with response from middleware
        """
        middleware = mock.MagicMock()
        self.service.add_incoming_middleware(middleware)
        res = mock.MagicMock(spec=messages.Response)
        middleware.process = mock.MagicMock(return_value=res)

        message = mock.MagicMock(spec=messages.IncomingRequestCall)
        method = "method"
        proxy = mock.MagicMock()

        self.service.process(method, message, proxy)
        route_mock.assert_not_called()
        send_mock.call_count = 1
