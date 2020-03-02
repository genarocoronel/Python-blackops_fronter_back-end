import abc
import email
import json
from dateutil.tz import gettz
from dateutil import parser as date_parser

import phonenumbers
from lxml import html as htmllib
from email.message import Message

from sqs_listener import SqsListener
import boto3

TEMP_EMAIL_FILE = '/tmp/email.txt'
PDF_FILE_TYPE = 'pdf'
AUDIO_FILE_TYPE = 'audio'


def find_part_by_content_type(message, content_type):
    for part in message.walk():
        if part.get_content_type() == content_type:
            return part
    return None


class Handler(abc.ABC):
    @abc.abstractmethod
    def handle(self, message):
        pass


class JiveFaxHandler(Handler):
    def handle(self, message):
        if not isinstance(message, email.message.Message):
            raise Exception('Expected to process email.message.Message object')

        part = find_part_by_content_type(message, "text/html")
        if part is None:
            raise Exception('Expected fax email to contain HTML content')

        payload = part.get_payload(decode=True)
        charset = part.get_content_charset()
        html = htmllib.fromstring(payload.decode(charset))

        received_date_raw = html.xpath('//div[contains(text(), "Time Received")]/following-sibling::div/text()')
        source_phone_raw = html.xpath('//div[contains(text(), "From")]/following-sibling::div/div/div[2]/a/text()')
        page_count_raw = html.xpath('//div[contains(text(), "Pages")]/following-sibling::div/text()')
        dest_phone_raw = html.xpath('//div[contains(text(), "To")]/following-sibling::div/div/div/a/text()')

        received_date = date_parser.parse(received_date_raw[0], tzinfos={'PDT': gettz('America/Los_Angeles'),
                                                                         'PST': gettz('America/Los_Angeles')})
        source_phone = phonenumbers.parse(source_phone_raw[0], None)
        dest_phone = phonenumbers.parse(dest_phone_raw[0], None)
        page_count = self._parse_page_count(page_count_raw)

        part = find_part_by_content_type(message, "application/pdf")
        fax_filename = part.get_filename()
        file_content = part.get_payload(decode=True)
        file_size = len(file_content)

        fax_dict = {
            'received_date': str(received_date),
            'source_phone': source_phone.national_number,
            'dest_phone': dest_phone.national_number,
            'page_count': page_count,
            'file_name': fax_filename,
            'file_size_bytes': file_size,
        }
        print(fax_dict)

        # TODO: write fax document to S3
        with open(f'/tmp/{fax_filename}', 'wb') as attachment:
            attachment.write(file_content)

    def _parse_page_count(self, page_count_raw):
        page_meta_parts = page_count_raw[0].split('(')
        page_count = int(page_meta_parts[0].strip())
        return page_count


class JiveVoicemailHandler(Handler):
    def handle(self, message):
        if not isinstance(message, email.message.Message):
            raise Exception('Expected to process email.message.Message object')

        print('HANDLING JIVE EMAIL WITH VOICEMAIL')
        pass


class JiveEmailHandler(Handler):
    def handle(self, message):
        print('HANDLING JIVE EMAIL')
        print(message)

        # TODO: Only allow whitelisted source emails to continue for processing

        queue_message = json.loads(message.get('Message'))
        action = queue_message['receipt']['action']
        bucket_name = action['bucketName']
        object_key = action['objectKey']

        resource = boto3.resource('s3')

        resource.Object(bucket_name, object_key).download_file(TEMP_EMAIL_FILE)
        with open(TEMP_EMAIL_FILE, 'r') as file:
            email_message = email.message_from_file(file)  # type: Message

        if email_message.is_multipart():
            parts = email_message.get_payload()
            for part in parts:
                content_type = part.get_content_maintype()
                sub_content_type = part.get_content_subtype()
                if content_type == AUDIO_FILE_TYPE:
                    voicemail_handler = JiveVoicemailHandler()
                    voicemail_handler.handle(email_message)
                    break

                if sub_content_type == PDF_FILE_TYPE:
                    fax_handler = JiveFaxHandler()
                    fax_handler.handle(email_message)
                    break

        else:
            raise Exception('Expected multipart message!')


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
        else:
            raise Exception('Unprocessable message received')

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
