from flask import request
from flask_restplus import Resource

from app.main.service.communication_service import parse_communication_types, date_range_filter, get_communication_records
from app.main.service.user_service import get_client_assignments, get_candidate_assignments, get_request_user
from app.main.util.decorator import token_required
from app.main.util.dto import CommunicationDto
from app.main.util.parsers import filter_request_parse

api = CommunicationDto.api
_communication = CommunicationDto.communication


@api.route('/')
class Communications(Resource):
    @token_required
    @api.marshal_list_with(_communication, envelope='data')
    @api.param('_dt', 'Comma separated date fields to be filtered')
    @api.param('_from', 'Start date of communications to query (YYYY-MM-DD)')
    @api.param('_to', 'End date of communications to query (YYYY-MM-DD)')
    @api.param('type', "Default is 'all'. Options are 'call', 'voicemail', or 'sms'")
    @api.doc(security='apikey')
    @api.doc('Get all forms of communication for candidates/clients assigned to current user')
    def get(self):
        """ Get all forms of communication for candidates/clients assigned to current user  """
        try:
            filter = filter_request_parse(request)
            comm_types_set = parse_communication_types(request)

            date_range_filter(filter)

            current_user = get_request_user()
            candidates = get_candidate_assignments(current_user)
            clients = get_client_assignments(current_user)

            date_filter_fields = filter.get('dt_fields', [])
            result = get_communication_records(filter, comm_types_set, candidates, clients, date_filter_fields)

            return sorted(result, key=lambda record: record.receive_date, reverse=True)

        except Exception as e:
            api.abort(500, message=f'Failed to retrieve communication records for {current_user.username}. Error: {e}', success=False)
