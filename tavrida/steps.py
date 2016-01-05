import controller
import messages


class ValidateMessageMiddleware(controller.AbstractController):
    """
    Validates message headers
    """

    def process(self, ampq_message):
        ampq_message.validate()
        return ampq_message


class CreateMessageMiddleware(controller.AbstractController):
    """
    Creates message from raw RabbitMQ message
    """

    def process(self, message_body):
        return messages.IncomingMessageFactory().create(message_body)


class CreateAMQPMiddleware(controller.AbstractController):
    """
    Creates intermediate AMQP message
    """

    def process(self, message):
        return messages.AMQPMessage.create_from_message(message)
