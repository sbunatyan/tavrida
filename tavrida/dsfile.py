import ConfigParser


class DSFileEntry(object):
    """Record contains information about service exchanges."""

    def __init__(self,
                 service_name,
                 service_exchange,
                 notifications_exchange=None):
        super(DSFileEntry, self).__init__()
        self._service_name = service_name
        self._service_exchange = service_exchange
        self._notifications_exchange = notifications_exchange

    @property
    def service_name(self):
        return self._service_name

    @property
    def service_exchange(self):
        return self._service_exchange

    @property
    def notifications_exchange(self):
        return self._notifications_exchange


class DSFile(object):
    """DSFile represents configuration file for Discovery Service.

    Configuration file has following format

      [service name]
      exchange=service exchange name
      notifications=service notifications exchange name (optional)

      [service name 2]
      ...

    You can use DSFile as a dict to get information about service by
    service name:
      dsf = dsfile.DSFile('dsfile.ini')
      print dsf['myservice'].service_exchange
      print dsf['myservice'].notifications_exchange

    You can get list of services using
        for service_name in dsf:
            ...
    or
        [x for x in dsf]
    or
        print list(dsf)
    or
        print dsf.services

    Raises ConfigParser.Error exception (or child exception) if input
    file is malformed.

    """
    def __init__(self, filepath):
        """
        :param filepath: file path
        :type filepath: string
        """
        super(DSFile, self).__init__()
        self._filepath = filepath
        # Map from service_name to DSFileEntry
        self._entries = self._load(self._filepath)

    def _load(self, filepath):
        """Parses file and returns entries map
        """
        entries = {}
        cp = ConfigParser.ConfigParser()
        # I don't use contextmanager here because context manager is
        # hard for testing.
        f = open(filepath)
        try:
            cp.readfp(f)
        finally:
            f.close()
        for service_name in cp.sections():
            service_exchange = cp.get(service_name, "exchange")
            try:
                notifications_exchange = cp.get(service_name, "notifications")
            except ConfigParser.NoOptionError:
                notifications_exchange = None
            entry = DSFileEntry(service_name,
                                service_exchange,
                                notifications_exchange)
            entries[entry.service_name] = entry
        return entries

    def __getitem__(self, service_name):
        return self._entries[service_name]

    @property
    def services(self):
        """Returns list of service names."""
        return self._entries.keys()

    def __iter__(self):
        return iter(self.services)
