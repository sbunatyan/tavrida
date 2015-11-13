import pika


class Credentials(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password


class ConnectionConfig(object):

    def __init__(self, host, credentials, port=5672, virtual_host="/",
                 channel_max=None,
                 frame_max=None, heartbeat_interval=None, ssl=None,
                 ssl_options=None, connection_attempts=3,
                 retry_delay=1.0, socket_timeout=3.0,
                 locale=None, backpressure_detection=None):
            self.host = host
            self.port = port
            self.virtual_host = virtual_host
            self.credentials = credentials
            self.channel_max = channel_max
            self.frame_max = frame_max
            self.heartbeat_interval = heartbeat_interval
            self.ssl = ssl
            self.ssl_options = ssl_options
            self.connection_attempts = connection_attempts
            self.retry_delay = retry_delay
            self.socket_timeout = socket_timeout
            self.locale = locale
            self.backpressure_detection = backpressure_detection

    def to_dict(self):
        return self.__dict__

    def to_pika_params(self):
        params = self.to_dict()
        params["credentials"] = pika.PlainCredentials(
            self.credentials.username, self.credentials.password)
        return pika.ConnectionParameters(**params)
