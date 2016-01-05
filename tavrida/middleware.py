import controller


class Middleware(controller.AbstractMessageController):

    """
    Base middleware class. Any middleware should be inherited from this class.
    Middlewares could be added for processing message before and after the
    handler call.
    """

    def process(self, message):
        """
        Processes message.
        This method should be redefined.

        :param message: incoming/outgoing message
        :type message: messages.Message
        :return: modified or new message
        :rtype: message.Message
        """
        return message
