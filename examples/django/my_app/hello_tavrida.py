from models import Hello, World

from tavrida import config
from tavrida import dispatcher
from tavrida import server
from tavrida import service


import logging

logging.basicConfig(level=logging.INFO)


@dispatcher.rpc_service("hello_service")
class HelloController(service.ServiceController):

    @dispatcher.rpc_method(service="hello_service", method="create")
    def create(self, request, proxy, value):
        # Handles test_hello.hello requests, then send request to
        # test_world.world method and published notification
        #
        h = Hello(value=value)
        h.save()
        print "Hello created: %s" % str(h)

    @dispatcher.rpc_method(service="hello_service", method="delete")
    def delete(self, request, proxy, uuid):
        # Handles test_hello.hello requests, then send request to
        # test_world.world method and published notification
        #
        hellos = Hello.objects.find(pk=uuid)
        if hellos:
            hellos[0].delete()
        print "Hello with uuid = %s deleted" % uuid

    @dispatcher.rpc_method(service="test_world", method="create")
    def create(self, request, proxy, value, parent_id):
        # Handles test_hello.hello requests, then send request to
        # test_world.world method and published notification
        #
        World(value=value, parent_id=parent_id).save()


def run_me():

    # FOR RPC AND SUBSCRIBE
    # ---------------------
    # start server on given queue and exchange
    # The given queue will be used to obtain messages from other services (rpc
    # and publishers).
    # The given exchange will be used by other services to send there it's
    # requests, responses, errors.

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds)

    srv = server.Server(conf,
                        queue_name="test_service",
                        exchange_name="test_exchange",
                        service_list=[HelloController])
    srv.run()
