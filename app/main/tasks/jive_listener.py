import abc

from sqs_listener import SqsListener


class Handler(abc.ABC):
    @abc.abstractmethod
    def handle(self, message):
        pass


class JiveEmailHandler(Handler):
    def handle(self, message):
        print('HANDLING JIVE EMAIL')
        print(message)


class JiveRecordingHandler(Handler):
    def handle(self, message):
        print('HANDLING JIVE RECORDING')
        print(message)


class JiveListener(SqsListener):
    JIVE_RECORDING_ID = 's3-thedeathstarco-jive-recording'
    JIVE_EMAIL_ID = 'ses-thedeathstarco-jive-received'

    def _identify_handler(self, message):
        topic_source = message.get('TopicArn').split(':')[-1]
        if topic_source == self.JIVE_RECORDING_ID:
            return JiveRecordingHandler()
        elif topic_source == self.JIVE_EMAIL_ID:
            return JiveEmailHandler()

    def handle_message(self, body, attributes, messages_attributes):
        handler = self._identify_handler(body)
        handler.handle(body)


def run():
    print("Initializing listener")
    listener = JiveListener('jive-listener', region_name='us-west-2', interval=10,
                            queue_url='https://sqs.us-west-2.amazonaws.com/450101876349/jive')
    listener.listen()


if __name__ == '__main__':
    run()