from flask import request
from flask_restplus import Resource

from ..util.dto import SmsDto
from app.main.service.sms_service import register_new_sms_mssg, get_convo, whois_webhook_token, \
    get_convo_for_client, send_message_to_client
from app.main.core.errors import BadRequestError, NotFoundError
from flask import current_app

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
            current_app.logger.info('Received request to register an SMS message by service provider.')
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
            current_app.logger.info(f"Received request to get SMS Conversation by its publid ID {convo_public_id}")
            convo_mssgs = get_convo(convo_public_id)

        except NotFoundError as e:
            api.abort(404, message='Error getting SMS conversation, {}'.format(str(e)), success=False)
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
            current_app.logger.info(f"Received request to get SMS Conversation by client public ID {client_public_id}")
            convo_mssgs = get_convo_for_client(client_public_id)

        except NotFoundError as e:
            api.abort(404, message='Error getting SMS conversation, {}'.format(str(e)), success=False)
        except Exception as e:
           api.abort(500, message=f'Failed to get a SMS Conversation for Client ID {client_public_id}', success=False)

        if not convo_mssgs:
            api.abort(404, message=f"Conversation for client with ID {client_public_id} does not exist", success=False, )

        return convo_mssgs, 200


@api.route('/client/<client_public_id>/send')
@api.param('client_public_id', 'Client public ID')
class SmsSendSendToClient(Resource):
    @api.doc('Send a SMS message to a Client')
    def post(self, client_public_id):
        if not client_public_id:
            return 'Bad request: the client ID was not given.', 400
        
        request_data = request.json
        to_phone = None
        if 'to_phone' in request_data and request_data['to_phone'] != None:
            to_phone = request_data['to_phone']
        from_phone = request_data['from_phone']
        messg_body = request_data['message_body']
        
        try:
            current_app.logger.info(f'Received request to send SMS message to client with ID {client_public_id}')
            sms_message = send_message_to_client(client_public_id, from_phone, messg_body, to_phone)
            return sms_message, 200
        except BadRequestError as e:
            api.abort(400, message='Error sending SMS to client, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error sending SMS to client, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to send SMS messge to Client with ID {client_public_id}', success=False)
