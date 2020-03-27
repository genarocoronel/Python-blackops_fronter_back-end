from flask import request
from flask_restplus import Resource

from ..util.dto import SmsDto
from app.main.service.sms_service import (register_new_sms_mssg, whois_webhook_token,
    get_convo_for_client, send_message_to_client, get_convo_for_candidate, send_message_to_candidate)
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
        """ Webhook for registering a new inbound SMS Message or update an outbound one with delivery status """
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
            sms_mssg = register_new_sms_mssg(mssg_data, provider_name)
            response = {
                'success': True,
                'message': "Successfully registered a Provider SMS message. Thank you.",
                'our_message_id': sms_mssg.public_id
            }
            return response, 200 

        except Exception as e:
            response = {
                'success': False,
                'message': "Failed to register a new Provider SMS message"
            }
            return response, 200


@api.route('/client/<client_public_id>/conversation/')
@api.param('client_public_id', 'Client public ID')
class SmsClientConversation(Resource):
    @api.doc('Get a SMS/MMS Conversation for a Lead/Client')
    def get(self, client_public_id):
        """ Get a SMS/MMS Conversation for a Lead/Client """
        try:
            current_app.logger.info(f"Received request to get SMS Conversation by client public ID {client_public_id}")
            convo_mssgs = get_convo_for_client(client_public_id)

        except NotFoundError as e:
            api.abort(404, message='Error getting SMS conversation, {}'.format(str(e)), success=False)
        except Exception as e:
           api.abort(500, message=f'Failed to get a SMS Conversation for Client ID {client_public_id}', success=False)

        return convo_mssgs, 200


@api.route('/client/<client_public_id>/send')
@api.param('client_public_id', 'Client public ID')
class SmsSendSendToClient(Resource):
    @api.doc('Send a SMS message to a Lead/Client')
    def post(self, client_public_id):
        """ Sends a SMS Message to a Lead/Client """
        if not client_public_id:
            return 'Bad request: the client ID was not given.', 400
        
        request_data = request.json
        # TODO - Refactor the from phone to reflect integration of PBX and user-assigned numbers
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


@api.route('/candidate/<candidate_public_id>/conversation/')
@api.param('candidate_public_id', 'Candidate public ID')
class SmsCandidateConversation(Resource):
    @api.doc('Get a SMS/MMS Conversation for a Candidate')
    def get(self, candidate_public_id):
        """ Get a SMS/MMS Conversation for a Candidate """
        try:
            current_app.logger.info(f"Received request to get SMS Conversation by Candidate public ID {candidate_public_id}")
            convo_mssgs = get_convo_for_candidate(candidate_public_id)

        except NotFoundError as e:
            api.abort(404, message='Error getting SMS conversation, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to get a SMS Conversation for Candidate ID {candidate_public_id}', success=False)

        return convo_mssgs, 200


@api.route('/candidate/<candidate_public_id>/send')
@api.param('candidate_public_id', 'Candidate public ID')
class SmsSendSendToCandidate(Resource):
    @api.doc('Send a SMS/MMS message to a Candidate')
    def post(self, candidate_public_id):
        if not candidate_public_id:
            return 'Bad request: the Candidate ID was not given.', 400
        
        request_data = request.json
        # TODO - Refactor the from phone to reflect integration of PBX and user-assigned numbers
        to_phone = None
        if 'to_phone' in request_data and request_data['to_phone'] != None:
            to_phone = request_data['to_phone']
        from_phone = request_data['from_phone']
        messg_body = request_data['message_body']
        
        try:
            current_app.logger.info(f'Received request to send SMS message to Candidate with ID {candidate_public_id}')
            sms_message = send_message_to_candidate(candidate_public_id, from_phone, messg_body, to_phone)
            return sms_message, 200
        except BadRequestError as e:
            api.abort(400, message='Error sending SMS to Candidate, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error sending SMS to Candidate, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to send SMS messge to Candidate with ID {candidate_public_id}', success=False)