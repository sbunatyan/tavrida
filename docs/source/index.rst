.. Tavrida documentation master file, created by
   sphinx-quickstart on Sat Jan  2 15:18:28 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Tavrida's documentation!
===================================

Source
------

https://github.com/sbunatyan/tavrida

Contents
--------

.. toctree::
   :maxdepth: 1

   tutorial
   controller
   messages
   middlewares
   discovery
   client
   proxy
   config


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Brief service example
---------------------

.. code-block:: python
    :linenos:

    from tavrida import config
    from tavrida import dispatcher
    from tavrida import server
    from tavrida import service

    @dispatcher.rpc_service("test_hello")
    class HelloController(service.ServiceController):

        @dispatcher.rpc_method(service="test_hello", method="hello")
        def handler(self, request, proxy, param):
            print param

    def run():

        creds = config.Credentials("guest", "guest")
        conf = config.ConnectionConfig("localhost", credentials=creds,
                                       async_engine=True)
        srv = server.Server(conf,
                            queue_name="test_service",
                            exchange_name="test_exchange",
                            service_list=[HelloController])
        srv.run()