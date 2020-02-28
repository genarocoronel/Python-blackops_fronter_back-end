from flask import request
from flask_restplus import Resource

from ..util.dto import SmsDto
from app.main.service.sms_service import register_new_sms_mssg, get_convo, whois_webhook_token, \
    get_convo_for_client

api = SmsDto.api
_new_sms_mssg_registration = SmsDto.new_sms_mssg_registration

@api.route('/register-message/<webhook_token>')
@api.param('webhook_token', 'Authorized webhook token for existing identity')
class SmsRegistration(Resource):
    @api.doc('Register a new SMS message')
    @api.expect(_new_sms_mssg_registration, validate=False)
    def post(self, webhook_token):
        request_data = request.json
        mssg_data = request_data[0]

        provider_name = whois_webhook_token(webhook_token)
        if not provider_name:
            return api.abort(401, 'Contact your service representative for credentials', success=False)

        if mssg_data is None:
            return api.abort(400, message='The message payload is missing.', success=False)

        # Bandwidth always must expect 200 HTTP code, except for when not using our webhook token
        try:
            response = register_new_sms_mssg(mssg_data, provider_name)
            return response, 200 

        except Exception as e:
            response_object = {
                'success': False,
                'message': "Failed to register a new Provider SMS message"
            }
            return response_object, 200
        

@api.route('/conversation/<convo_public_id>')
@api.param('convo_public_id', 'SMS conversation public ID')
class SmsConversation(Resource):
    @api.doc('Get a SMS/MMS Conversation')
    def get(self, convo_public_id):
        try:
            convo_mssgs = get_convo(convo_public_id)

        except Exception as e:
            api.abort(500, f'Failed to retrieve SMS Conversation with ID {convo_public_id}', success=False)

        if not convo_mssgs:
            api.abort(404, message=f"Conversation with ID {convo_public_id} does not exist", success=False)

        return convo_mssgs, 200


@api.route('/client/<client_public_id>/conversation/')
@api.param('client_public_id', 'Client public ID')
class SmsClientConversation(Resource):
    @api.doc('Get a SMS/MMS Conversation for a Client')
    def get(self, client_public_id):
        try:
            convo_mssgs = get_convo_for_client(client_public_id)

        except Exception as e:
           api.abort(500, message=f'Failed to get a SMS Conversation for Client ID {client_public_id}', success=False)

        if not convo_mssgs:
            api.abort(404, message=f"Conversation for client with ID {client_public_id} does not exist", success=False, )

        return convo_mssgs, 200
