import copy

UNKNOWN_ERROR = 1000
DEFAULT_ERROR_MESSAGE = "Unknown error occured"


class BaseException(Exception):

    _msg_template = DEFAULT_ERROR_MESSAGE
    _service_error_code = UNKNOWN_ERROR

    def __init__(self, **kwargs):
        super(BaseException, self).__init__()
        self._kwargs = kwargs

    def __str__(self):
        return self._msg_template % self._kwargs

    @property
    def message_template(self):
        return self._msg_template

    @property
    def kwargs(self):
        return copy.deepcopy(self._kwargs)

    @property
    def code(self):
        return self._service_error_code


class AckableException(object):
    pass


class BaseAckableException(BaseException, AckableException):
    pass


class FieldMustExist(BaseAckableException):

    _msg_template = "Field %(field)s must exists in message"
    _service_error_code = 1001


class FieldMustFullyDefined(BaseAckableException):

    _msg_template = "Field %(field)s must not contain null values"
    _service_error_code = 1003


class UnsuitableFieldValue(BaseAckableException):

    _msg_template = "Unsuitable field %(field)s value %(value)s"
    _service_error_code = 1002


class HandlerNotFound(BaseAckableException):

    _msg_template = "Handler for %(entry_point)s (%(message_type)s) not found"
    _service_error_code = 1004


class NeedToBeController(BaseException):

    _msg_template = "Service %(service)s should be of ServiceController class"
    _service_error_code = 1005


class WrongEntryPointFormat(BaseAckableException):

    _msg_template = "EntryPoint should be of pattern 'service.method'"
    _service_error_code = 1006


class UnableToDiscover(BaseAckableException):

    _msg_template = "Service %(service)s could not be discovered"
    _service_error_code = 1007


class IncorrectAMQPConfig(BaseException):

    _msg_template = "Wrong amqp url %(amqp_url)s"
    _service_error_code = 1008


class WrongResponse(BaseException):

    _msg_template = ("Got incorrect response %(response)s. sResponse should "
                     "be of types: Response, Error, dict.")
    _service_error_code = 1009


class IncorrectAMQPLibrary(BaseException):

    _msg_template = "Incorrect value for amqp library"
    _service_error_code = 1010


class ServiceNotFound(BaseAckableException):

    _msg_template = "Service for %(entry_point)s is not found"
    _service_error_code = 1022


class UnknownService(BaseAckableException):

    _msg_template = "Service %(service)s unknown for server"
    _service_error_code = 1022


class DuplicatedServiceRegistration(BaseAckableException):

    _msg_template = "Service %(service)s is already registered"
    _service_error_code = 1023


class DuplicatedEntryPointRegistration(BaseAckableException):

    _msg_template = "Service %(method)s is already registered"
    _service_error_code = 1024


class ServiceIsNotRegister(BaseAckableException):

    _msg_template = "Service %(service)s is not registered"
    _service_error_code = 1026


class PublisherEndpointNotFound(BaseAckableException):

    _msg_template = ("Remote Method (event) name for given handler "
                     "%(method_name)s is not found")
    _service_error_code = 1027


class DuplicatedMethodRegistration(BaseException):

    _msg_template = "Duplicated registration of method '%(method_name)s'"
    _service_error_code = 1028


class ForbiddenHeaders(BaseException):
    _msg_template = "Headers are forbidden to re-define %(headers)s"
    _service_error_code = 1029


class SubscriptionHandlerNotFound(BaseAckableException):
    _msg_template = "Subscription handler for %(entry_point)s is not found"
    _service_error_code = 1030
