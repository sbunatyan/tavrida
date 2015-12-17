class EntryPoint(object):

    """
    Describes service entry point.
    Stores service_name and method_name
    """

    def __init__(self, service_name, method_name, message_type=None):
        super(EntryPoint, self).__init__()
        self._service_name = service_name
        self._method_name = method_name
        self._message_type = message_type

    @property
    def service(self):
        return self._service_name

    @property
    def method(self):
        return self._method_name

    @property
    def message_type(self):
        return self._message_type

    def copy(self):
        return self.__class__(self.service, self.method, self.message_type)

    def __str__(self):
        if self.message_type:
            return '{0}.{1}.{2}'.format(self.service, self.method,
                                        self.message_type)
        else:
            return '{0}.{1}'.format(self.service, self.method)

    def __repr__(self):
        return self.__str__()

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

    def add_type(self, message_type):
        self._message_type = message_type


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

    def _create_entry_point(self, *parts):
        return EntryPoint(*parts)

    def _create_service(self, service_name):
        return ServiceEntryPoint(service_name)

    def _create_source(self, *parts):
        return Source(*parts)

    def _create_destination(self, *parts):
        return Destination(*parts)

    def _create_null(self):
        return NullEntryPoint()

    def create(self, value, source=False, destination=False):
        if isinstance(value, EntryPoint):
            return value

        if not value:
            return self._create_null()
        elif "." in value:
            parts = value.split(".")
            if source:
                return self._create_source(*parts)
            if destination:
                return self._create_destination(*parts)
            else:
                return self._create_entry_point(*parts)
        else:
            return self._create_service(value)
