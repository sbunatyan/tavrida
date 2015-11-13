import abc


class AbstractController(object):

    """
    Abstract controller should be used to implement arbitrary controllers in
    the chain of actions on some object
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def process(self, *args, **kwargs):
        pass


class AbstractMessageController(AbstractController):

    """
    Abstract controller should be used to implement arbitrary controllers in
    the chain of actions on message
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def process(self, message):
        """

        :param message:  Message of arbitrary type
        :return: Any result, mainly message
        """
        pass
