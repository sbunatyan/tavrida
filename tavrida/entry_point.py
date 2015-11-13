class EntryPoint(object):

    """
    Describes service entry point.
    Stores service_name and method_name
    """

    def __init__(self, service_name, method_name):
        super(EntryPoint, self).__init__()
        self._service_name = service_name
        self._method_name = method_name

    @property
    def service(self):
        return self._service_name

    @property
    def method(self):
        return self._method_name

    def copy(self):
        return self.__init__(self.service, self.method)

    def __str__(self):
        return '{0}.{1}'.format(self.service, self.method)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, EntryPoint):
            return False
        return (self.service == other.service and
                self.method == other.method)

    def hash(self):
        return str(self)

    def to_routing_key(self):
        return str(self)


class ServiceEntryPoint(EntryPoint):

    def __init__(self, service_name):
        super(ServiceEntryPoint, self).__init__(service_name, None)

    def __str__(self):
        return self.service


class NullEntryPoint(EntryPoint):

    def __init__(self):
        super(NullEntryPoint, self).__init__(None, None)

    def __str__(self):
        return ""

    def __nonzero__(self):
        return False

    def __eq__(self, other):
        return False

    def to_routing_key(self):
        raise NotImplemented


class Source(EntryPoint):
    pass


class Destination(EntryPoint):
    pass


class EntryPointFactory(object):

    def _create_entry_point(self, service_name, method_name):
        return EntryPoint(service_name, method_name)

    def _create_service(self, service_name):
        return ServiceEntryPoint(service_name)

    def _create_source(self, service_name, method_name):
        return Source(service_name, method_name)

    def _create_destination(self, service_name, method_name):
        return Destination(service_name, method_name)

    def _create_null(self):
        return NullEntryPoint()

    def create(self, string, source=False, destination=False):
        if "." in string:
            parts = string.split(".")
            if source:
                return self._create_source(*parts)
            if destination:
                return self._create_destination(*parts)
            else:
                return self._create_entry_point(*parts)
        elif string:
            return self._create_service(string)
        else:
            return self._create_null()
