import controller
import router


class Processor(controller.AbstractMessageController):

    """
    Processes message. This class is responsible for message transfer
    to the corresponding controller's method
    """

    def __init__(self, service_list):
        self._service_list = service_list

    def _get_router(self):
        return router.Router()

    def process(self, message):
        """
        Processes message. Provides it ro router

        :param message: incoming message
        :type message:messages.Message
        :return: response or None
        :rtype: messages.Response, messages.Error, None
        """
        router = self._get_router()
        return router.process(message, self._service_list)
