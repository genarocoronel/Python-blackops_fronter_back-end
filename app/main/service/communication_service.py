import datetime
import enum
import itertools
from dataclasses import dataclass
from typing import Union, List, AbstractSet, Mapping, Any

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import or_
from flask import current_app as app

from app.main.core.errors import ServiceProviderError
from app.main.model.candidate import CandidateVoiceCommunication, Candidate
from app.main.model.client import ClientVoiceCommunication, Client
from app.main.model.pbx import VoiceCommunicationType, TextCommunicationType, VoiceCommunication, CommunicationType
from app.main.model.sms import SMSMessage, SMSConvo
from app.main.util.query import build_query_from_dates

PAST_DAYS = -7


@dataclass
class TextMessage:
    public_id: str
    type: TextCommunicationType
    source_number: int
    destination_number: int
    outside_number: int
    body_text: str
    receive_date: datetime.datetime
    inserted_on: datetime.datetime
    is_viewed: bool


def _normalize_sms_comms(sms_comms: List[SMSMessage]):
    comms = []
    for sms in sms_comms:
        if sms.direction == 'in':
            source_number = sms.from_phone
            outside_number = sms.from_phone
            dest_number = sms.to_phone
        else:
            source_number = sms.to_phone
            dest_number = sms.from_phone
            outside_number = sms.from_phone

        comms.append(TextMessage(**{
            'public_id': sms.public_id,
            'type': TextCommunicationType.SMS,
            'source_number': source_number,
            'destination_number': dest_number,
            'outside_number': outside_number,
            'body_text': sms.body_text,
            'receive_date': sms.inserted_on,
            'inserted_on': sms.inserted_on,
            'is_viewed': sms.is_viewed
        }))
    return comms


class CommTypeMapping(enum.Enum):
    ALL = VoiceCommunicationType.RECORDING, VoiceCommunicationType.VOICEMAIL, TextCommunicationType.SMS
    CALL = VoiceCommunicationType.RECORDING,
    VOICEMAIL = VoiceCommunicationType.VOICEMAIL,
    SMS = TextCommunicationType.SMS,


def parse_communication_types(request):
    types_list = [CommTypeMapping[value.upper()] for value in str(request.args.get('type', 'all')).split(',')]
    types_set = set(itertools.chain(*[item.value for item in types_list]))
    return types_set


def get_client_voice_communications(clients: Union[Client, List[Client]],
                                    comm_types_set: AbstractSet[CommunicationType],
                                    date_filter_fields: List[str],
                                    request_filter: Mapping[str, Any]):
    client_comms_filter = ClientVoiceCommunication.query.join(VoiceCommunication)

    if clients:
        if isinstance(clients, list):
            client_comms_filter = client_comms_filter.filter(or_(ClientVoiceCommunication.client_id == client.id for client in clients))
        else:
            client_comms_filter = client_comms_filter.filter(ClientVoiceCommunication.client_id == clients.id)

    client_comms_filter = build_query_from_dates(client_comms_filter, request_filter['from_date'], request_filter['to_date'],
                                                 VoiceCommunication,
                                                 *date_filter_fields)
    client_comms_filter = client_comms_filter.filter(or_(
        VoiceCommunication.type == comm_type for comm_type in comm_types_set if isinstance(comm_type, VoiceCommunicationType))
    )
    client_voice_comms = client_comms_filter.all()
    return client_voice_comms


def get_candidate_voice_communications(candidates: Union[Candidate, List[Candidate]],
                                       comm_types_set: AbstractSet[CommunicationType],
                                       date_filter_fields: List[str],
                                       request_filter: Mapping[str, Any]):
    candidate_comms_filter = CandidateVoiceCommunication.query.join(VoiceCommunication)

    if candidates:
        if isinstance(candidates, list):
            candidate_comms_filter = candidate_comms_filter.filter(
                or_(CandidateVoiceCommunication.candidate_id == candidate.id for candidate in candidates))
        else:
            candidate_comms_filter = candidate_comms_filter.filter(CandidateVoiceCommunication.candidate_id == candidates.id)

    candidate_comms_filter = build_query_from_dates(candidate_comms_filter, request_filter['from_date'], request_filter['to_date'],
                                                    VoiceCommunication,
                                                    *date_filter_fields)
    candidate_comms_filter = candidate_comms_filter.filter(or_(
        VoiceCommunication.type == comm_type for comm_type in comm_types_set if isinstance(comm_type, VoiceCommunicationType))
    )
    candidate_voice_comms = candidate_comms_filter.all()
    return candidate_voice_comms


def get_candidate_sms_communications(candidates: Union[Candidate, List[Candidate]],
                                     date_filter_fields: List[str],
                                     request_filter: Mapping[str, Any]):
    candidate_comms_filter = SMSMessage.query.join(SMSConvo)

    if candidates:
        if isinstance(candidates, list):
            candidate_comms_filter = candidate_comms_filter.filter(
                or_(SMSConvo.candidate_id == candidate.id for candidate in candidates))
        else:
            candidate_comms_filter = candidate_comms_filter.filter(SMSConvo.candidate_id == candidates.id)

    candidate_comms_filter = build_query_from_dates(candidate_comms_filter, request_filter['from_date'], request_filter['to_date'],
                                                    SMSMessage,
                                                    *date_filter_fields)

    candidate_sms_comms = candidate_comms_filter.all()
    return candidate_sms_comms


def get_client_sms_communications(clients: Union[Client, List[Client]],
                                  date_filter_fields: List[str],
                                  request_filter: Mapping[str, Any]):
    client_comms_filter = SMSMessage.query.join(SMSConvo)

    if clients:
        if isinstance(clients, list):
            client_comms_filter = client_comms_filter.filter(
                or_(SMSConvo.client_id == client.id for client in clients))
        else:
            client_comms_filter = client_comms_filter.filter(SMSConvo.client_id == clients.id)

    client_comms_filter = build_query_from_dates(client_comms_filter, request_filter['from_date'], request_filter['to_date'],
                                                 SMSMessage,
                                                 *date_filter_fields)

    client_sms_comms = client_comms_filter.all()
    return client_sms_comms


def date_range_filter(request_filter):
    # default from_date if not present
    if 'from_date' not in request_filter:
        seven_days_ago = datetime.datetime.utcnow() + datetime.timedelta(days=PAST_DAYS)
        from_date = datetime.datetime(seven_days_ago.year, seven_days_ago.month, seven_days_ago.day, 0, 0, 0, 0,
                                      tzinfo=datetime.timezone.utc)
        request_filter['from_date'] = from_date

    # default to_date if not present
    if 'to_date' not in request_filter:
        request_filter['to_date'] = None


def get_communication_records(request_filter: Mapping[str, Any],
                              comm_types_set: AbstractSet[CommunicationType],
                              candidates: Union[Candidate, List[Candidate]] = None,
                              clients: Union[Client, List[Client]] = None,
                              date_filter_fields: List[str] = {}):
    """
    Aggregate all of the communication records between Opener, Sales, and Service
    """
    result = []
    result.extend(get_opener_communication_records(request_filter, comm_types_set, candidates, date_filter_fields))
    result.extend(get_sales_and_service_communication_records(request_filter, comm_types_set, clients, date_filter_fields))
    return result


def get_opener_communication_records(request_filter: Mapping[str, Any],
                                     comm_types_set: AbstractSet[CommunicationType],
                                     candidates: Union[Candidate, List[Candidate]] = None,
                                     date_filter_fields: List[str] = {}):
    result = []
    if any(isinstance(comm_type, VoiceCommunicationType) for comm_type in comm_types_set):
        candidate_voice_comms = get_candidate_voice_communications(candidates, comm_types_set, date_filter_fields, request_filter)
        result.extend([record.voice_communication for record in candidate_voice_comms])

    if any(isinstance(comm_type, TextCommunicationType) for comm_type in comm_types_set):
        candidate_sms_comms = _normalize_sms_comms(get_candidate_sms_communications(candidates, date_filter_fields, request_filter))
        result.extend([record for record in candidate_sms_comms])
    return result


def get_sales_and_service_communication_records(request_filter: Mapping[str, Any],
                                                comm_types_set: AbstractSet[CommunicationType],
                                                clients: Union[Client, List[Client]] = None,
                                                date_filter_fields: List[str] = {}):
    result = []
    if any(isinstance(comm_type, VoiceCommunicationType) for comm_type in comm_types_set):
        client_voice_comms = get_client_voice_communications(clients, comm_types_set, date_filter_fields, request_filter)
        result.extend([record.voice_communication for record in client_voice_comms])

    if any(isinstance(comm_type, TextCommunicationType) for comm_type in comm_types_set):
        client_sms_comms = _normalize_sms_comms(get_client_sms_communications(clients, date_filter_fields, request_filter))
        result.extend([record for record in client_sms_comms])
    return result


# TODO: consider tracking/caching URLs that have been generated for subsequent requests within expiration window
def create_presigned_url(voice_communication: VoiceCommunication, expiration=3600):
    """Generate a presigned URL to share an S3 object"""

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        url = s3_client.generate_presigned_url('get_object',
                                               Params={'Bucket': voice_communication.file_bucket_name,
                                                       'Key': voice_communication.file_bucket_key},
                                               ExpiresIn=expiration)
    except ClientError as e:
        app.logger.error(f'Failed to create presigned url for voice communication. Error: {e}')
        raise ServiceProviderError('Failed to create presigned URL to voice communication file')

    return url


def get_candidate_voice_communication(candidate: Candidate, voice_communication_public_id: str):
    candidate_voice_comm = CandidateVoiceCommunication.query.join(VoiceCommunication) \
        .filter(Candidate.id == candidate.id) \
        .filter(VoiceCommunication.public_id == voice_communication_public_id).first()
    if candidate_voice_comm:
        return candidate_voice_comm.voice_communication
    return None


def get_client_voice_communication(client: Client, voice_communication_public_id: str):
    client_voice_comm = ClientVoiceCommunication.query.join(VoiceCommunication) \
        .filter(Client.id == client.id) \
        .filter(VoiceCommunication.public_id == voice_communication_public_id).first()
    if client_voice_comm:
        return client_voice_comm.voice_communication
    return None


def get_voice_communication(voice_communication_id: str):
    return VoiceCommunication.query.filter_by(public_id=voice_communication_id).first()
