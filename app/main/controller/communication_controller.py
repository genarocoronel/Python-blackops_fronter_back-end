from flask import request, current_app as app
from flask_restplus import Resource
from werkzeug.exceptions import Unauthorized

from app.main.model.pbx import TextCommunicationType, VoiceCommunicationType, VoiceCallEvent
from app.main.service.communication_service import parse_communication_types, date_range_filter, \
    get_voice_communication, create_presigned_url, get_opener_communication_records, get_sales_and_service_communication_records, \
    get_communication_records, get_all_unassigned_voice_communication_records, update_voice_communication, \
    get_sales_and_service_unassigned_voice_communication_records, get_opener_unassigned_voice_communication_records, get_sms_communication, \
    update_sms_communication
from app.main.service.user_service import get_request_user
from app.main.util.decorator import token_required
from app.main.util.dto import CommunicationDto
from app.main.util.parsers import filter_request_parse

api = CommunicationDto.api
_communication = CommunicationDto.communication
_update_communication = CommunicationDto.update_communication

COMMUNICATION_RECORD_UPDATE_KEYS = 'is_viewed',


@api.route('/')
class Communications(Resource):
    @token_required
    @api.marshal_list_with(_communication, envelope='data')
    @api.param('_dt', 'Comma separated date fields to be filtered')
    @api.param('_from', 'Start date of communications to query (YYYY-MM-DD)')
    @api.param('_to', 'End date of communications to query (YYYY-MM-DD)')
    @api.param('type', "Default is 'all'. Options are 'call', 'voicemail', 'missed_call', or 'sms'")
    @api.param('is_viewed', "Filter records on whether or not it has been viewed. Default: all. Options: true, false, all")
    @api.doc(security='apikey')
    @api.doc('Get all forms of communication for candidates/clients depending on the requesting user')
    def get(self):
        """ Get all forms of communication for candidates/clients depending on the requesting user """
        current_user = get_request_user()

        try:
            filter = filter_request_parse(request)
            # TODO: look into leveraging filter object for is_viewed
            is_viewed = request.args.get('is_viewed', 'all')
            filter.update({'is_viewed': is_viewed})
            comm_types_set = parse_communication_types(request)

            date_range_filter(filter)

            if not current_user.is_manager and not current_user.is_admin:
                api.abort(401, message=f'{current_user.username} does not have permission to view this endpoint', success=False)

            date_filter_fields = filter.get('dt_fields', [])

            if current_user.is_opener_account:
                result = get_opener_communication_records(filter, comm_types_set, None, date_filter_fields)
                if current_user.is_manager and not current_user.is_admin:
                    result.extend(get_opener_unassigned_voice_communication_records(filter, comm_types_set, date_filter_fields))

            elif current_user.is_sales_account or current_user.is_service_account:
                result = get_sales_and_service_communication_records(filter, comm_types_set, None, date_filter_fields)
                if current_user.is_manager and not current_user.is_admin:
                    result.extend(get_sales_and_service_unassigned_voice_communication_records(filter, comm_types_set, date_filter_fields))

            else:
                # current_user has access to all data - get all communication records
                result = get_communication_records(filter, comm_types_set, None, None, date_filter_fields)

            if current_user.is_admin:
                result.extend(get_all_unassigned_voice_communication_records(filter, comm_types_set, date_filter_fields))

            return sorted(result, key=lambda record: record.receive_date, reverse=True)

        except Unauthorized:
            raise
        except Exception as e:
            api.abort(500, message=f'Failed to retrieve communication records for {current_user.username}. Error: {e}', success=False)


@api.route('/<communication_id>')
class CommunicationsRecord(Resource):
    @token_required
    @api.marshal_with(_communication)
    @api.param('type', "Options are 'voice' or 'text' (all others would be rolled up to their respective type)")
    @api.doc(security='apikey')
    @api.doc('Get individual communication record')
    def get(self, communication_id):
        """ Get communication record """

        comm_types_set = parse_communication_types(request)
        if len(comm_types_set) == 0:
            api.abort(400, message="'type is required", success=False)

        if len(list({type(comm_type) for comm_type in comm_types_set})) > 1:
            api.abort(400, message="Only one 'type' is valid", success=False)

        # TODO: limit retrieval of record to the respective user requesting

        comm_type = list(comm_types_set)[0]
        if isinstance(comm_type, TextCommunicationType):
            sms_comm_record = get_sms_communication(communication_id)
            if sms_comm_record is None:
                api.abort(404, message=f'Communication record does not exist', success=False)
            return sms_comm_record

        if isinstance(comm_type, VoiceCommunicationType):
            voice_comm_record = get_voice_communication(communication_id)
            if voice_comm_record is None:
                api.abort(404, message=f'Communication record does not exist', success=False)
            return voice_comm_record

        api.abort(400, message="Invalid communication type provided", success=False)

    @token_required
    @api.marshal_with(_communication)
    @api.expect(_update_communication)
    @api.param('type', "Options are 'voice' or 'text' (all others would be rolled up to their respective type)")
    @api.doc(security='apikey')
    @api.doc('Update individual communication record')
    def patch(self, communication_id):
        """ Update communication record """

        comm_types_set = parse_communication_types(request)
        if len(comm_types_set) == 0:
            api.abort(400, message="'type is required", success=False)

        if len(list({type(comm_type) for comm_type in comm_types_set})) > 1:
            self.abort = api.abort(400, message="Only one 'type' is valid", success=False)

        # TODO: limit update of record to the respective user requesting

        data = request.json
        update_attrs = {key: data[key] for key in data.keys() & COMMUNICATION_RECORD_UPDATE_KEYS}

        comm_type = list(comm_types_set)[0]
        if isinstance(comm_type, TextCommunicationType):
            sms_comm_record = get_sms_communication(communication_id)
            if sms_comm_record is None:
                api.abort(404, message=f'Communication record does not exist', success=False)
            return update_sms_communication(update_attrs, sms_communication=sms_comm_record)

        if isinstance(comm_type, VoiceCommunicationType):
            voice_comm_record = get_voice_communication(communication_id)
            if voice_comm_record is None:
                api.abort(404, message=f'Communication record does not exist', success=False)
            return update_voice_communication(update_attrs, voice_communication=voice_comm_record)

        api.abort(400, message="Invalid communication type provided", success=False)


@api.route('/<communication_id>/file')
class CommunicationsFile(Resource):
    @token_required
    @api.doc(security='apikey')
    @api.doc('Get communications audio file')
    def get(self, communication_id):
        """ Get voice communication file url """
        voice_communication = get_voice_communication(communication_id)
        if not voice_communication:
            api.abort(404, message='Voice communication not found', success=False)
        else:
            update_voice_communication({'is_viewed': True}, voice_communication=voice_communication)
            expiration_seconds = app.s3_signed_url_timeout_seconds
            file_url = create_presigned_url(voice_communication, expiration=expiration_seconds)
            response_object = {
                'success': True,
                'message': f'File URL will expire in {expiration_seconds / 60} minutes.',
                'file_url': file_url
            }
            return response_object, 200
