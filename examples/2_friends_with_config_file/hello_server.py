import logging

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


if __name__ == "__main__":
    srv = server.CLIServer("hello_config.cfg")
    srv.run()
