from tavrida import client
from tavrida import config
from tavrida import discovery
from tavrida import entry_point

creds = config.Credentials("guest", "guest")
conf = config.ConnectionConfig("localhost", credentials=creds)

# You should always provide source !!!
source = entry_point.Source("client", "method")


# You should provide discovery service object to client
disc = discovery.LocalDiscovery()
disc.register_remote_service(service_name="test_hello",
                             exchange_name="test_exchange")

cli = client.RPCClient(config=conf, discovery=disc, source=source)
cli.test_hello.hello(param=123).cast(correlation_id="123-456")

# If you want to provide source as a string
cli = client.RPCClient(config=conf, discovery=disc, source="source_service")
cli.test_hello.hello(param=123).cast(correlation_id="123-456")

cli = client.RPCClient(config=conf, discovery=disc, source="source.method")
cli.test_hello.hello(param=123).cast(correlation_id="123-456")
cli.test_hello.hello(param=123).cast(correlation_id="123-456")
cli.test_hello.hello(param=123).cast(correlation_id="123-456")

cli.close_connection()
