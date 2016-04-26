import logging

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

if __name__ == "__main__":
    # run process with --config-file=world_config.cfg parameter
    srv = server.CLIServer()
    srv.run()
