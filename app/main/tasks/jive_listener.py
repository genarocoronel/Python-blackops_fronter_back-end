import abc
import datetime
import email
import json
from urllib.parse import unquote

import pytz
from dateutil.tz import gettz
from dateutil import parser as date_parser
from pytimeparse import parse as time_parser

import phonenumbers
from lxml import html as htmllib
from email.message import Message

from sqs_listener import SqsListener
import boto3


from app.main.model.candidate import Candidate, CandidateContactNumber
from app.main.model.client import Client, ClientContactNumber
from app.main.model.contact_number import ContactNumber
from app.main.service.config_service import get_registered_pbx_numbers

TEMP_EMAIL_FILE = '/tmp/email.txt'
PDF_FILE_TYPE = 'pdf'
AUDIO_FILE_TYPE = 'audio'
DEFAULT_PHONE_REGION = 'US'


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
        source_phone = phonenumbers.parse(source_phone_raw[0], DEFAULT_PHONE_REGION)
        dest_phone = phonenumbers.parse(dest_phone_raw[0], DEFAULT_PHONE_REGION)
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
        # print(message)

        part = find_part_by_content_type(message, "text/html")
        if part is None:
            raise Exception('Expected fax email to contain HTML content')

        payload = part.get_payload(decode=True)
        charset = part.get_content_charset()
        html = htmllib.fromstring(payload.decode(charset))

        received_date_raw = html.xpath('//div[contains(text(), "Received on")]/following-sibling::div/text()')
        duration_raw = html.xpath('//div[contains(text(), "Duration")]/following-sibling::div/text()')
        dest_mailbox = html.xpath('//div[contains(text(), "Voicemail Box")]/following-sibling::div/text()')
        source_phone_raw = html.xpath('//div[contains(text(), "From")]/following-sibling::div/div[2]/a/text()')

        received_date = date_parser.parse(received_date_raw[0], tzinfos={'PDT': gettz('America/Los_Angeles'),
                                                                         'PST': gettz('America/Los_Angeles')})
        source_phone = phonenumbers.parse(source_phone_raw[0], DEFAULT_PHONE_REGION)
        duration_sec = time_parser(duration_raw[0])

        part = find_part_by_content_type(message, "audio/mpeg")
        audio_filename = part.get_filename()
        file_content = part.get_payload(decode=True)
        file_size = len(file_content)

        fax_dict = {
            'received_date': str(received_date),
            'source_phone': source_phone.national_number,
            'dest_mailbox': dest_mailbox[0],
            'duration_seconds': duration_sec,
            'file_name': audio_filename,
            'file_size_bytes': file_size,
        }
        print(fax_dict)

        # TODO: write voicemail file to S3
        with open(f'/tmp/{audio_filename}', 'wb') as attachment:
            attachment.write(file_content)


class JiveEmailHandler(Handler):
    def handle(self, message):
        print('HANDLING JIVE EMAIL')
        print(message)

        # TODO: Only allow whitelisted source emails to continue for processing

        queue_message = json.loads(message.get('Message'))
        action = queue_message['receipt']['action']
        bucket_name = action['bucketName']
        object_key = unquote(action['objectKey'])

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

        queue_message = json.loads(message.get('Message'))
        records = queue_message['Records']
        for record in records:
            bucket_name = record['s3']['bucket']['name']
            object_key = unquote(record['s3']['object']['key'])
            file_size_bytes = record['s3']['object']['size']

            s3 = boto3.client('s3')
            response = s3.head_object(Bucket=bucket_name, Key=object_key)
            response_meta = response['ResponseMetadata']
            headers = response_meta['HTTPHeaders']

            caller_id_name = headers.get('x-amz-meta-caller_id_name')
            caller_id_number = headers.get('x-amz-meta-caller_id_number')
            source_number = phonenumbers.parse(headers.get('x-amz-meta-from'), DEFAULT_PHONE_REGION)
            dialed_number = phonenumbers.parse(headers.get('x-amz-meta-dialed_number'), DEFAULT_PHONE_REGION)
            destination_number = phonenumbers.parse(headers.get('x-amz-meta-to'), DEFAULT_PHONE_REGION)
            timestamp_mill = int(headers.get('x-amz-meta-timestamp'))  # timestamp call completed recording
            recording_id = headers.get('x-amz-meta-recording_id')
            resource_group_id = headers.get('x-amz-meta-resource_group_id')  # PBX UUID
            timezone = headers.get('x-amz-meta-timezone')  # PBX timezone

            voice_recording_dict = {
                'caller_id_name': caller_id_name,
                'caller_id_number': caller_id_number,
                'source_phone': source_number.national_number,
                'dialed_phone': dialed_number.national_number,
                'destination_phone': destination_number.national_number,
                'received_date': str(datetime.datetime.fromtimestamp(timestamp_mill / 1000, tz=pytz.timezone(timezone))),
                'recording_id': recording_id,
                'resource_group_id': resource_group_id,
                'file_size_bytes': file_size_bytes
            }
            print(voice_recording_dict)

            registered_pbx_numbers = get_registered_pbx_numbers()  # <= known company numbers registered with PBX
            if source_number.national_number in registered_pbx_numbers:
                # TODO: attempt to match client/lead/candidate based on destination_phone
                client_cn = self._search_client_by_phone(voice_recording_dict['destination_phone'])

                if client_cn is not None:
                    pass

                candidate_cn = self._search_candidate_by_phone(voice_recording_dict['destination_phone'])

                # TODO: attempt to match employee belonging to source_phone (possibly caller_id)
                # TODO: greater confidence if known association to client/lead/candidate found above
                employee_matches = self._get_employees_routed_with(voice_recording_dict['destination_phone'])


            if destination_number.national_number in registered_pbx_numbers:
                # TODO: attempt to match employee belonging to destination_phone
                # TODO: greater confidence if known association to client/lead/candidate found above
                employee = self._search_employee_by_phone(voice_recording_dict['destination_phone'])

                # TODO: attempt to match client/lead/candidate based on source_phone
                client_cn = self._search_client_by_phone(voice_recording_dict['source_phone'])

                if client_cn is not None:
                    self._create_voice_comm_records(employee, voice_recording_dict['destination_phone'], client_cn.client,
                                                    client_cn.contact_number)
                    return

                candidate_cn = self._search_candidate_by_phone(voice_recording_dict['source_phone'])
                self._create_voice_comm_records(employee, voice_recording_dict['destination_phone'], candidate_cn.candidate,
                                                candidate_cn.contact_number)

            pass

    def _search_candidate_by_phone(self, phone_no):
        candidate_cn = CandidateContactNumber.query.join(Candidate) \
            .join(ContactNumber) \
            .filter(ContactNumber.phone_number == phone_no).first()
        return candidate_cn

    def _search_client_by_phone(self, phone_no):
        client_cn = ClientContactNumber.query.join(Client) \
            .join(ContactNumber) \
            .filter(ContactNumber.phone_number == phone_no).first()
        return client_cn

    def _search_employee_by_phone(self, phone_no):
        pass

    def _create_voice_comm_records(self, employee, employee_no, caller, caller_no):
        pass


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
