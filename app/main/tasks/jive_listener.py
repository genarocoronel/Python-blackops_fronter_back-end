import abc
import datetime
import email
import json
import logging
import tempfile
import uuid
from dataclasses import dataclass
from typing import Union
from urllib.parse import unquote

import pytz
from dateutil.tz import gettz
from dateutil import parser as date_parser
from flask import current_app
from phonenumbers import PhoneNumber
from pytimeparse import parse as time_parser

import phonenumbers
from mutagen.mp3 import MP3
from lxml import html as htmllib
from email.message import Message

from sqlalchemy import or_
from sqs_listener import SqsListener
import boto3

from app.main import db
from app.main.model.candidate import Candidate, CandidateVoiceCommunication, CandidateFaxCommunication
from app.main.model.client import Client, ClientVoiceCommunication, ClientFaxCommunication
from app.main.model.pbx import VoiceCommunication, CommunicationType, PBXNumber, FaxCommunication, VoiceCommunicationType, \
    TextCommunicationType, CallEventType, PBXSystem, PBXSystemVoiceCommunication, PBXSystemFaxCommunication
from app.main.model.user import User, UserVoiceCommunication, UserFaxCommunication
from app.main.service.communication_service import get_missed_call_event
from app.main.service.customer_service import identify_customer_by_phone
from app.main.service.user_service import get_user_by_mailbox_id
from app.main.service.docproc_service import create_doc_from_fax

comms_logger = logging.getLogger('comms_listener')

TEMP_EMAIL_FILE = '/tmp/email.txt'
PDF_FILE_TYPE = 'pdf'
AUDIO_FILE_TYPE = 'audio'
DEFAULT_PHONE_REGION = 'US'
DEFAULT_PBX_PROVIDER_NAME = 'JIVE'
CUSTOMER_TYPES = (Candidate, Client)
EMPLOYEE_TYPES = (User)


def find_part_by_content_type(message, content_type):
    for part in message.walk():
        if part.get_content_type() == content_type:
            return part
    return None


@dataclass
class CommunicationData:
    source_entity: Union[User, Client, Candidate]
    source_number: PhoneNumber
    destination_entity: Union[User, Client, Candidate]
    destination_number: PhoneNumber
    provider_name: str = DEFAULT_PBX_PROVIDER_NAME
    provider_record_id: str = None
    duration_seconds: int = 0
    receive_date: datetime.datetime = datetime.datetime.utcnow()
    file_size_bytes: int = 0
    s3_bucket_name: str = None
    s3_object_key: str = None


class Handler(abc.ABC):
    HANDLER_NAME = 'default'

    def __init__(self, pbx_system_name='UNKNOWN'):
        self.pbx_system_name = pbx_system_name

    @abc.abstractmethod
    def handle(self, message):
        pass

    def _build_communication_data(self, source_number, destination_number, employee_mailbox_id: str = None, employee_caller_id: str = None):
        assert source_number is not None

        employee = None

        # Client/Candidate called Employee (voicemail)
        if employee_mailbox_id:
            customer = identify_customer_by_phone(source_number)
            employee = get_user_by_mailbox_id(employee_mailbox_id)
            return CommunicationData(customer, source_number, employee, destination_number)

        customer = identify_customer_by_phone(destination_number)
        if customer is None:
            customer = identify_customer_by_phone(source_number)

        return CommunicationData(employee, source_number, customer, destination_number)

    def _create_comm_records(self, communication_data: CommunicationData, communication_type: CommunicationType):
        comms_logger.info('Saving voice communication records')

        assert communication_data is not None

        source = communication_data.source_entity
        source_number = communication_data.source_number
        destination = communication_data.destination_entity
        destination_number = communication_data.destination_number

        phone_number_list = [source_number, destination_number]

        # attempt to find PBX Number from both source and destination numbers
        pbx_number = PBXNumber.query.filter(
            or_(PBXNumber.number == number.national_number for number in phone_number_list if number)
        ).first()

        customer = next((entity for entity in (source, destination) if isinstance(entity, CUSTOMER_TYPES)), None)
        customer_number = next((number for number in (source_number, destination_number) if number and number.national_number != pbx_number), None)

        employee = next((entity for entity in (source, destination) if isinstance(entity, EMPLOYEE_TYPES)), None)
        employee_number = next((number for number in (source_number, destination_number) if number and number.national_number == pbx_number), None)

        comms_logger.info(f'Communication record is being associated to PBX System {self.pbx_system_name}')
        pbx_system = PBXSystem.query.filter_by(name=self.pbx_system_name).one_or_none()

        if communication_type in [VoiceCommunicationType.RECORDING, VoiceCommunicationType.VOICEMAIL]:
            missed_call_event = get_missed_call_event(customer_number, status=CallEventType.GOING_TO_VOICEMAIL,
                                                      based_on_date=communication_data.receive_date, time_lapse=240)

            if VoiceCommunicationType.RECORDING == communication_type and missed_call_event:
                # Not saving the recording since this was a missed call. Voicemail will be captured and saved
                comms_logger.warning(f"Recording is being discarded since a matching missed all event was found.")
                return

            if VoiceCommunicationType.VOICEMAIL == communication_type and missed_call_event:
                comms_logger.info(f"Found missed call event with public_id '{missed_call_event.public_id}' for {communication_type.value}.")
                missed_call_event.status = CallEventType.MISSED_VOICEMAIL
                db.session.add(missed_call_event)
            else:
                comms_logger.warn(
                    f'Unable to find corresponding missed call event for {communication_type.value} received. {communication_type.value.capitalize}:\n{communication_data}')

            new_voice_comm = VoiceCommunication(
                public_id=str(uuid.uuid4()),
                type=communication_type,
                inserted_on=datetime.datetime.utcnow(),
                updated_on=datetime.datetime.utcnow(),
                source_number=source_number.national_number,
                destination_number=destination_number.national_number if destination_number else None,
                outside_number=customer_number.national_number if customer_number else None,
                receive_date=communication_data.receive_date,
                pbx_number=pbx_number,
                provider_name=communication_data.provider_name,
                provider_record_id=communication_data.provider_record_id,
                duration_seconds=communication_data.duration_seconds,
                file_size_bytes=communication_data.file_size_bytes,
                file_bucket_name=communication_data.s3_bucket_name,
                file_bucket_key=communication_data.s3_object_key,
            )
            db.session.add(new_voice_comm)

            # Add association of voice communication to the corresponding PBX System it originated from
            if pbx_system:
                new_pbx_system_voice_comm_association = PBXSystemVoiceCommunication(
                    pbx_system=pbx_system,
                    voice_communication=new_voice_comm
                )
                db.session.add(new_pbx_system_voice_comm_association)

            if customer:
                if isinstance(customer, Client):
                    new_client_communication = ClientVoiceCommunication(client=customer, voice_communication=new_voice_comm)
                    db.session.add(new_client_communication)
                elif isinstance(customer, Candidate):
                    new_candidate_communication = CandidateVoiceCommunication(candidate=customer, voice_communication=new_voice_comm)
                    db.session.add(new_candidate_communication)
                else:
                    comms_logger.warning(f'Unsupported customer type of ${type(customer)} found!')

            if employee:
                new_employee_communication = UserVoiceCommunication(user=employee, voice_communication=new_voice_comm)
                db.session.add(new_employee_communication)

        if communication_type in [TextCommunicationType.FAX]:
            new_fax_comm = FaxCommunication(
                public_id=str(uuid.uuid4()),
                inserted_on=datetime.datetime.utcnow(),
                updated_on=datetime.datetime.utcnow(),
                source_number=source_number.national_number,
                destination_number=destination_number.national_number if destination_number else None,
                outside_number=customer_number.national_number if customer_number else None,
                receive_date=communication_data.receive_date,
                pbx_number=pbx_number,
                provider_name=communication_data.provider_name,
                file_size_bytes=communication_data.file_size_bytes,
                file_bucket_name=communication_data.s3_bucket_name,
                file_bucket_key=communication_data.s3_object_key,
            )
            db.session.add(new_fax_comm)

            # Add association of fax communication to the corresponding PBX System it originated from
            if pbx_system:
                new_pbx_system_voice_comm_association = PBXSystemFaxCommunication(
                    pbx_system=pbx_system,
                    fax_communication=new_fax_comm
                )
                db.session.add(new_pbx_system_voice_comm_association)

            if customer:
                if isinstance(customer, Client):
                    new_client_communication = ClientFaxCommunication(client=customer, fax_communication=new_fax_comm)
                    db.session.add(new_client_communication)
                elif isinstance(customer, Candidate):
                    new_candidate_communication = CandidateFaxCommunication(candidate=customer, fax_communication=new_fax_comm)
                    db.session.add(new_candidate_communication)
                else:
                    comms_logger.warning(f'Unsupported customer type of ${type(customer)} found!')

            if employee:
                new_employee_communication = UserFaxCommunication(user=employee, fax_communication=new_fax_comm)
                db.session.add(new_employee_communication)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            comms_logger.error(f'Failed to save voice recording: Error: {e}')
            raise Exception('Failed to save voice recording!')


class JiveFaxHandler(Handler):
    HANDLER_NAME = 'jive-fax-handler'

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

        received_date = date_parser.parse(received_date_raw[0], tzinfos={'PST': gettz('America/Los_Angeles')})
        source_number = phonenumbers.parse(source_phone_raw[0], DEFAULT_PHONE_REGION)
        destination_number = phonenumbers.parse(dest_phone_raw[0], DEFAULT_PHONE_REGION)
        page_count = self._parse_page_count(page_count_raw)

        part = find_part_by_content_type(message, "application/pdf")
        fax_filename = part.get_filename()
        file_content = part.get_payload(decode=True)
        file_size = len(file_content)

        with open(f'/tmp/{fax_filename}', 'wb') as attachment:
            attachment.write(file_content)

        s3 = boto3.client('s3')
        bucket_name = current_app.s3_bucket_fax
        fax_object_key = f'{received_date.strftime("%Y-%m-%dT%H%M%S")}~fax~{uuid.uuid4()}.{fax_filename.split(".")[-1]}'

        with open(f'/tmp/{fax_filename}', 'rb') as data:
            comms_logger.debug(f'Uploading file to bucket \'{bucket_name}\'')
            s3.upload_fileobj(data, bucket_name, fax_object_key)
            comms_logger.debug(f'Fax file {fax_filename} uploaded to S3 bucket {bucket_name} with key {fax_object_key}')

        communication_data = self._build_communication_data(source_number, destination_number)
        communication_data.receive_date = received_date.astimezone(pytz.UTC)
        communication_data.file_size_bytes = file_size
        communication_data.s3_bucket_name = bucket_name
        communication_data.s3_object_key = fax_object_key

        self._create_comm_records(communication_data, TextCommunicationType.FAX)
        comms_logger.info('Fax capture completed!')

        create_doc_from_fax(communication_data.s3_object_key)

    def _parse_page_count(self, page_count_raw):
        page_meta_parts = page_count_raw[0].split('(')
        page_count = int(page_meta_parts[0].strip())
        return page_count


class JiveVoicemailHandler(Handler):
    HANDLER_NAME = 'jive-voicemail-handler'

    def handle(self, message):
        comms_logger.info('Handling PBX voicemail recording...')

        if not isinstance(message, email.message.Message):
            comms_logger.error(f'Unexpected message of type \'{type(message)}\' was received')
            raise Exception('Expected to process email.message.Message object')

        part = find_part_by_content_type(message, "text/html")
        if part is None:
            raise Exception('Expected fax email to contain HTML content')

        payload = part.get_payload(decode=True)
        charset = part.get_content_charset()
        html = htmllib.fromstring(payload.decode(charset))

        received_date_raw = html.xpath('//td[contains(text(), "Time")]/following-sibling::td/text()')
        duration_raw = html.xpath('//td[contains(text(), "Duration")]/following-sibling::td/text()')
        dest_mailbox = html.xpath('//td[contains(text(), "Voicemail box")]/following-sibling::td/text()')[0]
        source_phone_raw = html.xpath('//td[contains(text(), "From")]/following-sibling::td/text()')

        received_date = date_parser.parse(received_date_raw[0]).replace(tzinfo=gettz('America/Los_Angeles'))
        source_number = phonenumbers.parse(source_phone_raw[0].split(" ", 1)[-1], DEFAULT_PHONE_REGION)
        duration_seconds = time_parser(duration_raw[0].replace("&nbsp;", ' '))

        part = find_part_by_content_type(message, "audio/mpeg")
        audio_filename = part.get_filename()
        file_content = part.get_payload(decode=True)
        file_size = len(file_content)

        with open(f'/tmp/{audio_filename}', 'wb') as attachment:
            attachment.write(file_content)

        s3 = boto3.client('s3')
        bucket_name = current_app.s3_bucket_voicemail
        voicemail_object_key = f'{received_date.strftime("%Y-%m-%dT%H%M%S")}~voicemail~{uuid.uuid4()}.{audio_filename.split(".")[-1]}'

        with open(f'/tmp/{audio_filename}', 'rb') as data:
            comms_logger.debug(f'Uploading voicemail file {audio_filename} to S3 bucket {bucket_name} with key {voicemail_object_key}')
            s3.upload_fileobj(data, bucket_name, voicemail_object_key)
            comms_logger.debug(f'Voicemail file successfully uploaded')

        communication_data = self._build_communication_data(source_number, None, employee_mailbox_id=dest_mailbox)
        communication_data.receive_date = received_date.astimezone(pytz.UTC)
        communication_data.duration_seconds = duration_seconds
        communication_data.file_size_bytes = file_size
        communication_data.s3_bucket_name = bucket_name
        communication_data.s3_object_key = voicemail_object_key

        self._create_comm_records(communication_data, VoiceCommunicationType.VOICEMAIL)
        comms_logger.info('Voicemail capture completed!')


class JiveEmailHandler(Handler):
    HANDLER_NAME = 'jive-email-handler'

    def handle(self, message):
        comms_logger.info('Handling PBX email...')
        comms_logger.debug(f'Received message:\n{message}')

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
                    voicemail_handler = JiveVoicemailHandler(self.pbx_system_name)
                    voicemail_handler.handle(email_message)
                    break

                if sub_content_type == PDF_FILE_TYPE:
                    fax_handler = JiveFaxHandler(self.pbx_system_name)
                    fax_handler.handle(email_message)
                    break

        else:
            raise Exception('Expected multipart message!')


class JiveRecordingHandler(Handler):
    HANDLER_NAME = 'jive-recording-handler'

    def handle(self, message):
        comms_logger.info('Handling PBX voice recording...')
        comms_logger.debug(f'Received message:\n{message}')

        queue_message = json.loads(message.get('Message'))
        records = queue_message['Records']
        for record in records:
            bucket_name = record['s3']['bucket']['name']
            object_key = unquote(record['s3']['object']['key'])
            file_size_bytes = record['s3']['object']['size']
            comms_logger.info(f'Processing object in S3 bucket \'{bucket_name}\' and object key \'{object_key}\'...')

            s3 = boto3.client('s3')
            response = s3.head_object(Bucket=bucket_name, Key=object_key)
            response_meta = response['ResponseMetadata']
            headers = response_meta['HTTPHeaders']

            # caller_id_name = headers.get('x-amz-meta-caller_id_name')
            # caller_id_number = headers.get('x-amz-meta-caller_id_number')
            source_number = phonenumbers.parse(headers.get('x-amz-meta-from'), DEFAULT_PHONE_REGION)
            # dialed_number = phonenumbers.parse(headers.get('x-amz-meta-dialed_number'), DEFAULT_PHONE_REGION)
            destination_number = phonenumbers.parse(headers.get('x-amz-meta-to'), DEFAULT_PHONE_REGION)
            timestamp_mill = int(headers.get('x-amz-meta-timestamp'))  # timestamp call completed recording
            recording_id = headers.get('x-amz-meta-recording_id')
            # resource_group_id = headers.get('x-amz-meta-resource_group_id')  # PBX UUID
            timezone = headers.get('x-amz-meta-timezone')  # PBX timezone

            with tempfile.TemporaryFile() as temp:
                s3.download_fileobj(bucket_name, object_key, temp)
                audio = MP3(temp)
                duration_seconds = int(audio.info.length)

            received_date = datetime.datetime.fromtimestamp(timestamp_mill / 1000, tz=pytz.timezone(timezone))
            communication_data = self._build_communication_data(source_number, destination_number)
            communication_data.provider_record_id = recording_id
            communication_data.receive_date = received_date.astimezone(pytz.UTC)
            communication_data.file_size_bytes = file_size_bytes
            communication_data.duration_seconds = duration_seconds
            communication_data.s3_bucket_name = bucket_name
            communication_data.s3_object_key = object_key
            self._create_comm_records(communication_data, VoiceCommunicationType.RECORDING)

        comms_logger.info('Voice recordings capture completed!')


class UnprocessableMessageException(Exception):
    pass


class JiveListener(SqsListener):
    def _identify_handler(self, message):
        topic_source = message.get('TopicArn').split(':')[-1]
        handler_info = current_app.comms_topic_to_handler_map.get(topic_source, None)

        if handler_info is None:
            comms_logger.error(f'Received unknown message: Message:\n{message}')
            raise Exception('Unknown message encountered. Unable to process.')

        handlers = (cls for cls in Handler.__subclasses__())
        for handler in handlers:
            if handler_info['handler_name'] == handler.HANDLER_NAME:
                return handler(handler_info['pbx_system_name'])

        comms_logger.warning(f'Missing handler with name: {handler_info["handler_name"]}')
        raise Exception(f'Missing Handler: {handler_info["handler_name"]}')

    def handle_message(self, body, attributes, messages_attributes):
        try:
            handler = self._identify_handler(body)
            handler.handle(body)
        except UnprocessableMessageException:
            comms_logger.error('Unprocessable message received')
            return


def _verify_configuration():
    if current_app.comms_topic_to_handler_map is None:
        comms_logger.error('Missing configuration from environment: COMMS_HANDLER_MAP')
        raise Exception('Missing required Config: COMMS_HANDLER_MAP')
    else:
        comms_logger.info(f'ENV[COMMS_HANDLER_MAP] = {current_app.comms_topic_to_handler_map}')


def run():
    _verify_configuration()
    comms_logger.info("Initializing listener")
    listener = JiveListener('jive-listener', region_name='us-west-2', interval=10, queue_url=current_app.jive_queue_url)
    comms_logger.info(f'Listening to {current_app.jive_queue_url}')
    listener.listen()


if __name__ == '__main__':
    run()
