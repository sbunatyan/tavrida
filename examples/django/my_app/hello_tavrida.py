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
        h = Hello(value=value)
        h.save()
        print "Hello created: %s" % str(h)

    @dispatcher.rpc_method(service="hello_service", method="delete")
    def delete(self, request, proxy, uuid):
        hellos = Hello.objects.find(pk=uuid)
        if hellos:
            hellos[0].delete()
        print "Hello with uuid = %s deleted" % uuid


@dispatcher.rpc_service("world_service")
class WorldController(service.ServiceController):

    @dispatcher.rpc_method(service="world_service", method="create")
    def create_world(self, request, proxy, value, parent_id):
        w = World(value=value, parent_id=parent_id)
        w.save()
        print "World created: %s" % w


def run_me():

    creds = config.Credentials("guest", "guest")
    conf = config.ConnectionConfig("localhost", credentials=creds,
                                   async_engine=True)

    srv = server.Server(conf,
                        queue_name="test_service",
                        exchange_name="test_exchange",
                        service_list=[HelloController,
                                      WorldController])
    srv.run()
