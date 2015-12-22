import logging

import controller
import steps


class PreProcessor(controller.AbstractController):

    """
    Preprocesses incoming messages. This class is responsible for message
    transfer to processor
    """

    def __init__(self, router, service_list):
        super(PreProcessor, self).__init__()
        self.log = logging.getLogger(__name__)
        self._router = router
        self._service_list = service_list
        self._steps = [
            steps.ValidateMessageMiddleware(),
            steps.CreateMessageMiddleware()
        ]

    @property
    def processor(self):
        return self._processor

    def process(self, amqp_message):
        """
        PreProcesses incoming message

        :param amqp_message: AMPQ message
        :type amqp_message: messages.AMQPMEssage
        :return: response object ot None
        :rtype: Response, Error or None
        """
        msg = amqp_message
        all_controllers = self._steps
        for step in all_controllers:
            msg = step.process(msg)
        self._router.process(msg, self._service_list)
