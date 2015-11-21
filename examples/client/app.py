from tavrida import client
from tavrida import config
from tavrida import discovery
from tavrida import entry_point

creds = config.Credentials("guest", "guest")
conf = config.ConnectionConfig("localhost", credentials=creds)

# You should always provide source !!!
source = entry_point.Source("client", "method")


cli = client.RPCClient(config=conf, service="test_hello",
                       exchange="test_exchange", source=source,
                       headers={"aaa": "bbb"})
cli.hello(param=123).cast(correlation_id="123-456")

# Or if you want to provide source as a string
cli = client.RPCClient(config=conf, service="test_hello",
                       exchange="test_exchange", source="source_service")
cli.hello(param=123).cast(correlation_id="123-456")

cli = client.RPCClient(config=conf, service="test_hello",
                       exchange="test_exchange", source="source.method")
cli.hello(param=123).cast(correlation_id="123-456")

# Also you can provide discovery service object to client
disc = discovery.LocalDiscovery()
disc.register_remote_service(service_name="test_hello",
                             exchange_name="test_exchange")
cli = client.RPCClient(config=conf, service="test_hello", discovery=disc,
                       source=source)
cli.hello(param=123).cast(correlation_id="123-456")
