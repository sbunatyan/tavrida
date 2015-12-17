import abc

import controller
import dispatcher
import messages


class ServiceController(controller.AbstractController):

    __metaclass__ = abc.ABCMeta

    _dispatcher = None

    def __init__(self, preprocessor, postprocessor):
        super(ServiceController, self).__init__()
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor

    @classmethod
    def get_dispatcher(cls):
        if not cls._dispatcher:
            cls._dispatcher = dispatcher.Dispatcher()
        return cls._dispatcher

    def process(self, method, message, proxy):
        if isinstance(message, messages.IncomingError):
            return getattr(self, method)(message, proxy)
        else:
            return getattr(self, method)(message, proxy, **message.payload)
