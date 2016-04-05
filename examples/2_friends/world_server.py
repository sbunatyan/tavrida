import logging

from tavrida import config
from tavrida import discovery
from tavrida import dispatcher
from tavrida import server
from tavrida import service


logging.basicConfig(level=logging.INFO)


@dispatcher.rpc_service("test_world")
class WorldController(service.ServiceController):

    @dispatcher.rpc_method(service="test_world", method="world")
    def world(self, request, proxy, param):
        print "---- request to world------"
        print request.context
        print request.headers
        print param
        print "---------------------------"
        return {"param": "world response"}

    @dispatcher.rpc_method(service="test_world", method="world2")
    def world2(self, request, proxy, param):
        print "---- request to world 2 ------"
        print request.context
        print request.headers
        print param
        print "---------------------------"

    @dispatcher.rpc_error_method(service="test_hello",
                                 method="hello_with_error")
    def hello_error(self, error, proxy):
        # Handles hello_with_error.hello errors
        print "---- error from hello ------"
        print error.context
        print error.headers
        print error.payload
        print "----------------------------"

    @dispatcher.subscription_method(service="test_hello", method="hello")
    def hello_subscription(self, notification, proxy, param):
        print "---- notification to world------"
        print notification.context
        print notification.headers
        print param
        print "---------------------------"
        proxy.test_hello.hello_with_error(param="555").call()


@dispatcher.rpc_service("test_chuck_norris")
class ChuckController(service.ServiceController):

    @dispatcher.rpc_method(service="test_chuck_norris", method="strike")
    def strike(self, request, proxy, param):
        print "---- request to strike------"
        print request.context
        print request.headers
        print param
        print "---------------------------"
        return {"param": "strike response"}

    @dispatcher.rpc_error_method(service="test_hello",
                                 method="hello_with_error")
    def hello_error(self, error, proxy):
        # Handles hello_with_error.hello errors
        print "---- error from hello to chuck_norris ------"
        print error.context
        print error.headers
        print error.payload
        print "----------------------------"

    @dispatcher.subscription_method(service="test_hello", method="hello")
    def hello_subscription(self, notification, proxy, param):
        print "---- notification to chuck_norris ------"
        print notification.context
        print notification.headers
        print param
        print "---------------------------"
        proxy.test_hello.hello_with_error(param="strike-456").call()

disc = discovery.LocalDiscovery()

# FOR RPC
# -------
# register remote service's exchanges to send there requests (RPC calls)
disc.register_remote_service("test_hello", "test_exchange")

# FOR SUBSCRIBE
# -------------
# register remote notification exchange to bind to it and get notifications
# In this example service 'test_subscribe' gets notifications to it's queue
# from 'test_notification_exchange' which is the publication exchange of
# service 'test_hello'
disc.register_remote_publisher("test_hello", "test_notification_exchange")

# FOR RPC AND SUBSCRIBE
# ---------------------
# start server on given queue and exchange
# The given queue will be used to obtain messages from other services (rpc
# and publishers).
# The given exchange will be used by other services to send there it's
# requests, responses, errors.

creds = config.Credentials("guest", "guest")
conf = config.ConnectionConfig("localhost", credentials=creds)
WorldController.set_discovery(disc)
ChuckController.set_discovery(disc)
srv = server.Server(conf,
                    queue_name="test_world_service",
                    exchange_name="test_world_exchange",
                    service_list=[WorldController, ChuckController])
srv.run()
