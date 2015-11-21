import controller
import messages


class ValidateMessageMiddleware(controller.AbstractController):

    def process(self, ampq_message):
        ampq_message.validate()
        return ampq_message


class CreateMessageMiddleware(controller.AbstractController):

    def process(self, message_body):
        return messages.IncomingMessageFactory().create(message_body)


class CreateAMQPMiddleware(controller.AbstractController):

    def process(self, message):
        return messages.AMQPMessage.create_from_message(message)
