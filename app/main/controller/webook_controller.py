import datetime
import uuid

import phonenumbers
from flask import request, make_response
from flask_restplus import Resource

from app.main import db
from app.main.model.pbx import VoiceCallEvent, CallEventType
from flask import current_app as app
from app.main.util.dto import WebhookDto

api = WebhookDto.api
_call_initiated_notification = WebhookDto.call_initiated
_call_missed_notification = WebhookDto.call_missed

DEFAULT_PHONE_REGION = 'US'


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

    def _get_call_numbers(self, request):
        args = request.args

        caller_number = args.get('caller', None)
        dialed_number = args.get('dialed', None)

        assert caller_number is not None
        assert dialed_number is not None

        return caller_number, dialed_number

    def _create_or_update_call_event(self, pbx_call_id, request, call_status: CallEventType):
        request_data = request.json
        caller_number, dialed_number = self._get_call_numbers(request)

        call_event = VoiceCallEvent.query.filter_by(pbx_call_id=pbx_call_id).first()
        if call_event:
            app.logger.info(f"Call event for {call_event.public_id} is being updated with '{call_status.name}'")

            call_event.updated_on = datetime.datetime.utcnow()
            call_event.status = call_status
        else:
            app.logger.warn(f"Call event for PBX Call ID '{pbx_call_id}' does not exist")
            app.logger.info(f"Call event is being created with '{call_status.name}'")
            call_event = VoiceCallEvent(
                public_id=str(uuid.uuid4()),
                pbx_id=request_data.get('pbx_id'),
                pbx_call_id=pbx_call_id,
                caller_number=phonenumbers.parse(caller_number, DEFAULT_PHONE_REGION).national_number,
                dialed_number=phonenumbers.parse(dialed_number, DEFAULT_PHONE_REGION).national_number,
                inserted_on=datetime.datetime.utcnow(),
                updated_on=datetime.datetime.utcnow(),
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
        request_data = request.json
        pbx_call_id = request_data.get('call_id')
        app.logger.info(f"Initiated Call event notification received for PBX Call ID '{pbx_call_id}'")
        app.logger.debug(f"Notification Message: \n{request_data}")

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
        request_data = request.json
        pbx_call_id = request_data.get('call_id')
        app.logger.info(f"Missed Call event notification received for PBX Call ID '{pbx_call_id}'")
        app.logger.debug(f"Notification Message: \n{request_data}")

        self._create_or_update_call_event(pbx_call_id, request, CallEventType.GOING_TO_VOICEMAIL)

        # return '', 204
        resp = make_response('', 204)
        resp.headers['Content-Length'] = 0
        return resp
