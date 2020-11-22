import datetime
import urllib.parse
import uuid

import phonenumbers
from flask import request, make_response
from flask_restplus import Resource

from app.main import db
from app.main.core import DEFAULT_PHONE_REGION
from app.main.model.pbx import VoiceCallEvent, CallEventType
from flask import current_app as app

from app.main.service.client_service import get_client_contact_by_phone, get_lead_assigned_employee
from app.main.util.dto import WebhookDto

api = WebhookDto.api
_call_initiated_notification = WebhookDto.call_initiated
_call_missed_notification = WebhookDto.call_missed
_call_route_request = WebhookDto.call_route_request


class WebhookResource(Resource):
    """
    CALL_ID	Unique string of characters used to identify the call (in POST Body = Y)
    CALLER_ID_NAME	Caller's name (in POST Body = Y).
    CALLER_ID_NUMBER	Caller's number (in POST Body = Y
    CNAM	Caller's name (in POST Body = N)
    CNUM	Caller's number (in POST Body = N)
    DIALED_NUMBER	Number the caller dialed (in POST Body = Y)
    DNIS	Number the caller dialed (in POST Body = N)
    PBX_ID	ID of the PBX receiving the call (in POST Body = Y)
    """

    def _get_call_id(self, request):
        request_data = request.form
        pbx_call_id = request_data.get('call_id', None) or request_data.get('CALL_ID', None)

        assert pbx_call_id is not None

        app.logger.info(f"Initiated Call event notification received for PBX Call ID '{pbx_call_id}'")
        app.logger.debug(f"Notification Message: \n{request_data}")
        return pbx_call_id

    def _get_call_numbers(self, request):
        args = request.args
        form = request.form

        caller_number_str = args.get('caller', None) or form.get('CALLER_ID_NUMBER', None)
        dialed_number_str = args.get('dialed', None) or form.get('DIALED_NUMBER', None)

        assert caller_number_str is not None
        assert dialed_number_str is not None

        caller_number = phonenumbers.parse(urllib.parse.unquote_plus(caller_number_str), DEFAULT_PHONE_REGION)
        dialed_number = phonenumbers.parse(urllib.parse.unquote_plus(dialed_number_str), DEFAULT_PHONE_REGION)

        return caller_number, dialed_number

    def _create_or_update_call_event(self, pbx_call_id, request, call_status: CallEventType):
        request_data = request.form
        caller_number, dialed_number = self._get_call_numbers(request)

        call_event = VoiceCallEvent.query.filter_by(pbx_call_id=pbx_call_id).first()
        utcnow = datetime.datetime.utcnow()
        if call_event:
            app.logger.info(f"Call event for {call_event.public_id} is being updated with '{call_status.name}'")

            call_event.updated_on = utcnow
            call_event.receive_date = utcnow,
            call_event.status = call_status
        else:
            app.logger.warn(f"Call event for PBX Call ID '{pbx_call_id}' does not exist")
            app.logger.info(f"Call event is being created with '{call_status.name}'")
            call_event = VoiceCallEvent(
                public_id=str(uuid.uuid4()),
                pbx_id=request_data.get('pbx_id', None) or request_data.get('PBX_ID'),
                pbx_call_id=pbx_call_id,
                caller_number=caller_number.national_number,
                dialed_number=dialed_number.national_number,
                receive_date=utcnow,
                inserted_on=utcnow,
                updated_on=utcnow,
                status=call_status
            )

        db.session.add(call_event)
        db.session.commit()


@api.route('/call-initiated')
class CallInitiatedWebhookResource(WebhookResource):
    @api.doc('notify system of a call being initiated')
    @api.param('caller', 'Caller phone number')
    @api.param('dialed', 'Dialed phone number')
    @api.expect(_call_initiated_notification, validate=True)
    def post(self):
        """ Webhook for notifying a Call has been initiated from the PBX provider """
        pbx_call_id = self._get_call_id(request)
        self._create_or_update_call_event(pbx_call_id, request, CallEventType.INITIATED)

        # return '', 204
        resp = make_response('', 204)
        resp.headers['Content-Length'] = 0
        return resp


@api.route('/call-missed')
class CallMissedWebhookResource(WebhookResource):
    @api.doc('notify system of a call being missed')
    @api.param('caller', 'Caller phone number')
    @api.param('dialed', 'Dialed phone number')
    @api.expect(_call_missed_notification, validate=True)
    def post(self):
        """ Webhook for notifying a Call has been missed from the PBX provider """
        pbx_call_id = self._get_call_id(request)
        self._create_or_update_call_event(pbx_call_id, request, CallEventType.INITIATED)

        self._create_or_update_call_event(pbx_call_id, request, CallEventType.GOING_TO_VOICEMAIL)

        # return '', 204
        resp = make_response('', 204)
        resp.headers['Content-Length'] = 0
        return resp


@api.route('/route-call')
class RouteCallWebHookResource(WebhookResource):
    @api.doc('request for call to be routed')
    @api.param('caller', 'Caller phone number')
    @api.param('dialed', 'Dialed phone number')
    @api.expect(_call_route_request, validate=True)
    def post(self):
        """ Webhook for notifying a Call is requesting to be routed """

        caller_number, _ = self._get_call_numbers(request)

        client_contact = get_client_contact_by_phone(caller_number)
        if not client_contact:
            resp = make_response('', 204)
            resp.headers['Content-Length'] = 0
            resp.headers['Content-Type'] = 'text/plain'
            return resp

        # TODO: modify behavior when routing in other departments is supported
        #  currently -> only look for assigned leads; clients in Service would most likely call direct line for their assigned employee
        #  reference: https://app.asana.com/0/1145671275220852/1154169158060944/f
        assigned_employee = get_lead_assigned_employee(client_contact.client_id)
        if assigned_employee:
            extension = assigned_employee.pbx_mailbox_id
            resp = make_response(extension, 200)
            resp.headers['Content-Type'] = 'text/plain'
        else:
            resp = make_response('', 204)
            resp.headers['Content-Length'] = 0
            resp.headers['Content-Type'] = 'text/plain'

        return resp
