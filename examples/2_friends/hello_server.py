import logging

from tavrida import config
from tavrida import discovery
from tavrida import dispatcher
from tavrida import server
from tavrida import service

logging.basicConfig(level=logging.INFO)


@dispatcher.rpc_service("test_hello")
class HelloController(service.ServiceController):

    @dispatcher.rpc_method(service="test_hello", method="hello")
    def hello1(self, request, proxy, param):
        # Handles test_hello.hello requests, then send request to
        # test_world.world method and published notification
        #
        print "---- request to hello ------"
        print request.context
        print request.headers
        print param
        print "----------------------------"
        proxy.test_world.world(param="proxy call - 1").call()
        proxy.test_world.world(param="proxy call - 2").transfer(request)
        proxy.publish(param="hello publication")
        print "======"

    @dispatcher.rpc_method(service="test_hello", method="hello_with_error")
    def hello_with_error(self, request, proxy, param):
        # Handles hello_with_error.hello requests and produces error
        print "---- request to hello with error ----"
        print request.context
        print request.headers
        print param
        print "-------------------------------------"
        raise Exception

    @dispatcher.rpc_response_method(service="test_world", method="world")
    def world_resp(self, response, proxy, param):
        # Handles responses for call made from test_hello.hello
        print "---- response from world to hello ----"
        print response.context
        print response.headers
        print param
        print "--------------------------------------"
        proxy.test_world.world2(param="proxy call - 3").call()


disc = discovery.LocalDiscovery()

# FOR RPC
# -------
# register remote service's exchanges to send there requests (RPC calls)
disc.register_remote_service("test_world", "test_world_exchange")
disc.register_remote_service("test_chuck_norris", "test_world_exchange")

# FOR PUBLICATIONS
# ----------------
# register service's notification exchange to publish notifications
# Service 'test_hello' publishes notifications to it's exchange
# 'test_notification_exchange'
disc.register_local_publisher("test_hello", "test_notification_exchange")

# FOR RPC AND SUBSCRIBE
# ---------------------
# start server on given queue and exchange
# The given queue will be used to obtain messages from other services (rpc
# and publishers).
# The given exchange will be used by other services to send there it's
# requests, responses, errors.

creds = config.Credentials("guest", "guest")
conf = config.ConnectionConfig("localhost", credentials=creds,
                               async_engine=True)
HelloController.set_discovery(disc)
srv = server.Server(conf,
                    queue_name="test_service", exchange_name="test_exchange",
                    service_list=[HelloController])
srv.run()
