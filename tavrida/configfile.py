import ast
import sys
import traceback

from oslo_config import cfg

from tavrida import exceptions


server_group = cfg.OptGroup(name='server', title='Server config')
connection_group = cfg.OptGroup(name='connection', title='General '
                                                         'RabbitMQ '
                                                         'connection '
                                                         'config')
ssl_group = cfg.OptGroup(name='ssl', title='Pika ssl config')

server_opts = [
    cfg.StrOpt('queue_name', help='Server queue name', required=True),
    cfg.StrOpt('exchange_name', help='Server exchange name', required=True),
    cfg.StrOpt('services', help='List of dictionaries describing services',
               required=True),
    cfg.StrOpt('discovery', help='discovery file path or URL', required=True,
               default=None),
]

connection_opts = [
    cfg.StrOpt('host', help='RabbitMQ host', required=True),
    cfg.StrOpt('username', help='RabbitMQ username', required=True),
    cfg.StrOpt('password', help='RabbitMQ password', required=True),
    cfg.IntOpt('port', help='RabbitMQ port', required=True, default=5672),
    cfg.StrOpt('virtual_host', help='RabbitMQ virtual host', required=True,
               default="/"),
    cfg.IntOpt('heartbeat_interval', help='RabbitMQ heartbeat interval (secs)',
               required=True,
               default=10),
    cfg.IntOpt('connection_attempts',
               help='RabbitMQ connection attempts number', required=True,
               default=3),
    cfg.IntOpt('channel_max', help='RabbitMQ maximum channel count value'),
    cfg.IntOpt('frame_max', help='The maximum byte size for an AMQP frame'),
    cfg.FloatOpt('retry_delay', help='RabbitMQ connection retry delay',
                 required=True, default=1.0),
    cfg.FloatOpt('socket_timeout', help='RabbitMQ socket timeout',
                 required=True, default=3.0),
    cfg.StrOpt('locale', help='RabbitMQ locale value'),
    cfg.BoolOpt('backpressure_detection', help='Toggle RabbitMQ backpressure '
                                               'detection'),
    cfg.BoolOpt('ssl', help='Enable SSL for RabbitMQ connection',
                default=False),
    cfg.IntOpt('reconnect_attempts', help='Attempts to reconnect to RabbitMQ',
               required=True, default=-1),
    cfg.BoolOpt('async_engine', help='Use async server engine', required=True,
                default=False)
]

ssl_opts = [
    cfg.StrOpt('keyfile', help='SSL keyfile'),
    cfg.StrOpt('certfile', help='SSL certfile'),
    cfg.IntOpt('cert_reqs', help='Whether a certificate is required from'
                                 ' RabbitMQ. Values set: 0, 1, 2'),
    cfg.IntOpt('ssl_version', help='SSL version. Values set: 1, 2, 3'),
    cfg.StrOpt('ca_certs', help='File containing a set of concatenated '
                                '"certification authority" certificates'),
    cfg.BoolOpt('suppress_ragged_eofs', help='specifies how the '
                                             'SSLSocket.read() method should '
                                             'signal unexpected EOF',
                default=True),
    cfg.StrOpt('ciphers', help='available SSL ciphers')
]


CONF = cfg.CONF
CONF.register_group(server_group)
CONF.register_opts(server_opts, server_group)
CONF.register_group(connection_group)
CONF.register_opts(connection_opts, connection_group)
CONF.register_group(ssl_group)
CONF.register_opts(ssl_opts, ssl_group)


def import_class(import_str):
    """
    Returns a class from a string

    :param import_str: class full name
    :type import_str: basestring
    :return: imported class
    :rtype: class
    """

    if "." in import_str:
        mod_str, _sep, class_str = import_str.rpartition('.')
    else:
        mod_str = "__main__"
        class_str = import_str

    try:
        cls_in_main = getattr(sys.modules["__main__"], class_str)
        if cls_in_main and cls_in_main.__name__ != class_str:
            __import__(mod_str)
            return getattr(sys.modules[mod_str], class_str)
        else:
            return getattr(sys.modules["__main__"], class_str)
    except AttributeError:
        raise ImportError('Class %s cannot be found (%s)' %
                          (class_str,
                           traceback.format_exception(*sys.exc_info())))


def get_config(args, project_name=None, config_file=None):
    """
    Sets the config file for configuration global variable and returns config
    file path

    :param args: command line arguments
    :type args: list
    :param project_name: name of project (optional)
    :type project_name: string
    :param config_file: config file path
    :type config_file: string
    :return: config file path
    :rtype: string
    """
    if config_file or args:
        config_file = [config_file]
    else:
        raise exceptions.ConfigFileIsNotDefined
    cfg.CONF(args=args, project=project_name, default_config_files=config_file)
    return cfg.CONF.config_file


def get_services():
    """
    Returns list of service dictionaries from config file

    :return: list of services
    :rtype: list of dicts
    """
    return ast.literal_eval(CONF.server.services)


def get_services_controllers():
    """
    Returns names of services' controller classes

    :return: names of services' controller classes
    :rtype: list of strings
    """
    return list(map(lambda x: x.get("controller"), get_services()))


def get_services_names():
    """
    Returns names of services

    :return: names of services
    :rtype: list of strings
    """
    return list(map(lambda x: x.get("name"), get_services()))


def get_services_classes():
    """
    Returns services' controller classes

    :return: services' controller classes
    :rtype: list of classes
    """
    return list(map(import_class, get_services_controllers()))


def get_service_name_class_mapping():
    """
    Returns mapping service name -> service controller class

    :return: mapping service name -> service controller class
    :rtype: dict
    """
    names = get_services_names()
    classes = get_services_classes()
    return dict(zip(names, classes))
