from sqs_listener import SqsListener


def run_my_function(body):
    print(body)


class MyListener(SqsListener):
    def handle_message(self, body, attributes, messages_attributes):
        run_my_function(body)


def run():
    print("Initializing listener")
    listener = MyListener('jive-emails', region_name='us-west-2', interval=60,
                          queue_url='https://sqs.us-west-2.amazonaws.com/450101876349/jive-emails')
    listener.listen()
