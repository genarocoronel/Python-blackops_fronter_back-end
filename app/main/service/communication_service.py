import datetime
import enum
import itertools
from typing import Union, List

from sqlalchemy import or_

from app.main.model.candidate import CandidateVoiceCommunication, Candidate
from app.main.model.client import ClientVoiceCommunication, Client
from app.main.model.pbx import VoiceCommunicationType, TextCommunicationType, VoiceCommunication
from app.main.util.query import build_query_from_dates

PAST_DAYS = -7


class CommTypeMapping(enum.Enum):
    ALL = VoiceCommunicationType.RECORDING, VoiceCommunicationType.VOICEMAIL, TextCommunicationType.SMS
    CALL = VoiceCommunicationType.RECORDING,
    VOICEMAIL = VoiceCommunicationType.VOICEMAIL,
    SMS = TextCommunicationType.SMS,


def parse_communication_types(request):
    types_list = [CommTypeMapping[value.upper()] for value in str(request.args.get('type', 'all')).split(',')]
    types_set = set(itertools.chain(*[item.value for item in types_list]))
    return types_set


def get_client_communications(clients: Union[Client, List[Client]], comm_types_set, date_filter_fields, filter):
    client_comms_filter = ClientVoiceCommunication.query.join(VoiceCommunication)

    if isinstance(clients, list):
        client_comms_filter = client_comms_filter.filter(or_(Client.id == client.id for client in clients))
    else:
        client_comms_filter = client_comms_filter.filter(Client.id == clients.id)

    client_comms_filter = build_query_from_dates(client_comms_filter, filter['from_date'], filter['to_date'], VoiceCommunication,
                                                 *date_filter_fields)
    client_comms_filter = client_comms_filter.filter(or_(
        VoiceCommunication.type == comm_type for comm_type in comm_types_set if isinstance(comm_type, VoiceCommunicationType))
    )
    client_voice_comms = client_comms_filter.all()
    return client_voice_comms


def get_candidate_communications(candidates: Union[Candidate, List[Candidate]], comm_types_set, date_filter_fields, filter):
    candidate_comms_filter = CandidateVoiceCommunication.query.join(VoiceCommunication)

    if isinstance(candidates, list):
        candidate_comms_filter = candidate_comms_filter.filter(
            or_(Candidate.id == candidate.id for candidate in candidates))
    else:
        candidate_comms_filter = candidate_comms_filter.filter(Candidate.id == candidates.id)

    candidate_comms_filter = build_query_from_dates(candidate_comms_filter, filter['from_date'], filter['to_date'],
                                                    VoiceCommunication,
                                                    *date_filter_fields)
    candidate_comms_filter = candidate_comms_filter.filter(or_(
        VoiceCommunication.type == comm_type for comm_type in comm_types_set if isinstance(comm_type, VoiceCommunicationType))
    )
    candidate_voice_comms = candidate_comms_filter.all()
    return candidate_voice_comms


def date_range_filter(filter):
    # default from_date if not present
    if 'from_date' not in filter:
        seven_days_ago = datetime.datetime.utcnow() + datetime.timedelta(days=PAST_DAYS)
        from_date = datetime.datetime(seven_days_ago.year, seven_days_ago.month, seven_days_ago.day, 0, 0, 0, 0,
                                      tzinfo=datetime.timezone.utc)
        filter['from_date'] = from_date

    # default to_date if not present
    if 'to_date' not in filter:
        filter['to_date'] = None