# Tavrida
RPC &amp; Pub/Sub over AMQP
[![Build Status](https://travis-ci.org/sbunatyan/tavrida.svg?branch=master)](https://travis-ci.org/sbunatyan/tavrida)

# Documentation

See http://tavrida.readthedocs.org/

# Brief example

Service Hello

	@dispatcher.rpc_service("test_hello")
	class HelloController(service.ServiceController):

		@dispatcher.rpc_method(service="test_hello", method="hello")
		def hello(self, request, proxy, param):
		    # Handles test_hello.hello requests, then send request to
		    # test_world.world method and published notification
		    print request.context, request.headers, param

            #make another call
		    proxy.test_world.world(param="proxy call").call()

            # publish notification
		    proxy.publish(param="hello publication")

            return {"key": "value"}

		@dispatcher.rpc_method(service="test_hello", method="hello_with_error")
		def hello_with_error(self, request, proxy, param):
		    # Handles hello_with_error.hello requests and produces error
                    # The result of such handler is error message
		    raise Exception

		@dispatcher.rpc_response_method(service="test_world", method="world")
		def world_resp(self, response, proxy, param):
		    # Handles responses from world "method" of "test_world" service
		    print "---- response from world to hello ----"

Service World

	@dispatcher.rpc_service("test_world")
	class WorldController(service.ServiceController):

		@dispatcher.rpc_method(service="test_world", method="world")
		def world(self, request, proxy, param):
		    print "---- request to world------"
			# call ho hello
			proxy.hello.hello_with_error(param=123).call()
		    return {"param": "world response"}

		@dispatcher.rpc_error_method(serive="test_hello", method="hello_with_error")
		def hello_error(self, error, proxy):
		    # Handles hello_with_error.hello errors
		    print "---- error from hello ------"
		    print error.payload
		    print "----------------------------"

		@dispatcher.subscription_method(service="test_hello", method="hello")
		def hello_subscription(self, notification, proxy, param):
		    print "---- notification from hello ------"
		    print param
		    print "---------------------------"