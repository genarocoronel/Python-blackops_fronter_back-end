from flask import request, g
from flask_restplus import Resource

from app.main.model.pbx import VoiceCommunicationType
from app.main.model.user import User
from app.main.service.communication_service import parse_communication_types, get_client_communications, get_candidate_communications, \
    date_range_filter
from app.main.service.user_service import get_client_assignments, get_candidate_assignments
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

            # TODO: should modify flask context to set the 'current_user' to a User model instance
            current_user = User.query.filter_by(id=g.current_user['user_id']).first()

            candidates = get_candidate_assignments(current_user)
            clients = get_client_assignments(current_user)

            date_filter_fields = filter.get('dt_fields', [])
            result = []
            if any(isinstance(comm_type, VoiceCommunicationType) for comm_type in comm_types_set):

                candidate_voice_comms = get_candidate_communications(candidates, comm_types_set, date_filter_fields, filter)
                client_voice_comms = get_client_communications(clients, comm_types_set, date_filter_fields, filter)
                result = [record.voice_communication for record in candidate_voice_comms + client_voice_comms]

            # TODO: check if SMS communication is requested and add to the result

            return result

        except Exception as e:
            api.abort(500, message=f'Failed to retrieve communication records for {g.current_user["username"]}. Error: {e}', success=False)
