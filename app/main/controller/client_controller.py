from flask import current_app as app
from flask import request
from flask_restplus import Resource

from app.main.controller import _convert_payload_datetime_values, _handle_get_client, _handle_get_credit_report
from app.main.core.errors import (BadRequestError, NotFoundError, ServiceProviderError, ServiceProviderLockedError)
from app.main.core.types import CustomerType
from app.main.model.client import ClientType
from app.main.service.client_service import (get_all_clients, save_new_client, get_client, get_client_appointments,
                                             update_client, get_client_employments, update_client_employments, get_client_income_sources,
                                             update_client_income_sources, get_client_monthly_expenses, update_client_monthly_expenses,
                                             update_client_addresses, get_client_addresses, get_client_contact_numbers,
                                             update_client_contact_numbers)
from app.main.service.communication_service import parse_communication_types, date_range_filter, get_communication_records, \
    get_client_voice_communication, create_presigned_url
from app.main.service.credit_report_account_service import (creport_account_signup, update_credit_report_account,
                                                            get_verification_questions, answer_verification_questions,
                                                            get_security_questions, complete_signup, pull_credit_report)
from app.main.service.debt_payment_service import contract_open_revision, contract_reinstate
from app.main.service.debt_service import check_existing_scrape_task, get_report_data
from app.main.service.debt_service import scrape_credit_report
from app.main.service.svc_schedule_service import create_svc_schedule, get_svc_schedule, update_svc_schedule
from app.main.service.user_service import get_request_user
from app.main.util.parsers import filter_request_parse
from ..util.decorator import token_required
from ..util.dto import ClientDto, AppointmentDto

api = ClientDto.api
_client = ClientDto.client
_update_client = ClientDto.update_client
_client_employment = ClientDto.client_employment
_update_client_employment = ClientDto.update_client_employment
_appointment = AppointmentDto.appointment
_client_income = ClientDto.client_income
_update_client_income = ClientDto.update_client_income
_client_monthly_expense = ClientDto.client_monthly_expense
_update_client_monthly_expense = ClientDto.update_client_monthly_expense
_credit_report_debt = ClientDto.credit_report_debt
_update_client_address = ClientDto.update_client_address
_contact_number = ClientDto.contact_number
_update_contact_number = ClientDto.update_contact_number
_client_address = ClientDto.client_address
_communication = ClientDto.communication
_new_credit_report_account = ClientDto.new_credit_report_account
_update_credit_report_account = ClientDto.update_credit_report_account
_credit_account_verification_answers = ClientDto.account_verification_answers

CLIENT = ClientType.client


@api.route('/')
class ClientList(Resource):
    @api.doc('list_of_clients')
    @api.marshal_list_with(_client, envelope='data')
    def get(self):
        """ List all clients """
        clients = get_all_clients(client_type=CLIENT)
        return clients

    @api.response(201, 'Client successfully created')
    @api.doc('create new client')
    @api.expect(_client, validate=True)
    def post(self):
        """ Creates new Client """
        data = request.json
        return save_new_client(data=data, client_type=CLIENT)


@api.route('/<public_id>')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Client not found')
class Client(Resource):
    @api.doc('get client')
    @api.marshal_with(_client)
    def get(self, public_id):
        """ Get client with provided identifier"""
        client, error_response = _handle_get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            return client

    @api.doc('update client')
    @api.expect(_update_client, validate=True)
    def put(self, public_id):
        """ Update client with provided identifier"""
        client = get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404)
        else:
            return update_client(client, request.json, client_type=CLIENT)


@api.route('/<client_id>/income-sources')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientIncomeSources(Resource):
    @api.doc('get client income sources')
    @api.marshal_list_with(_client_income)
    def get(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_income_sources(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update client income sources')
    @api.expect([_update_client_income], validate=True)
    def put(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            numbers = request.json
            result, err_msg = update_client_income_sources(client, numbers)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<client_id>/monthly-expenses')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientMonthlyExpenses(Resource):
    @api.doc('get client monthly expenses')
    @api.marshal_list_with(_client_monthly_expense)
    def get(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_monthly_expenses(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update client monthly expenses')
    @api.expect([_update_client_monthly_expense], validate=True)
    def put(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            expenses = request.json
            result, err_msg = update_client_monthly_expenses(client, expenses)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<public_id>/appointments')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Client not found')
class ClientAppointmentList(Resource):
    @api.doc('get client')
    @api.marshal_with(_appointment)
    def get(self, public_id):
        """ Get client appointments """
        result = get_client_appointments(public_id, client_type=CLIENT)
        if result is None:
            api.abort(404)
        else:
            return result


@api.route('/<public_id>/employments')
@api.param('public_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientEmployments(Resource):
    @api.doc('get client employments')
    @api.marshal_list_with(_client_employment)
    def get(self, public_id):
        client, error_response = _handle_get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_employments(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update client employment')
    @api.expect([_update_client_employment], validate=True)
    def put(self, public_id):
        client, error_response = _handle_get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            employments = request.json
            _convert_payload_datetime_values(employments, 'start_date', 'end_date')

            result, err_msg = update_client_employments(client, employments)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<client_id>/contact_numbers')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class LeadContactNumbers(Resource):
    @api.doc('Get Client contact numbers')
    @api.marshal_list_with(_contact_number)
    def get(self, client_id):
        client, error_response = _handle_get_client(client_id, client_type=ClientType.client)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_contact_numbers(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('Update Client contact numbers')
    @api.expect([_update_contact_number], validate=True)
    def put(self, client_id):
        client, error_response = _handle_get_client(client_id, client_type=ClientType.client)
        if not client:
            api.abort(404, **error_response)
        else:
            numbers = request.json
            result, err_msg = update_client_contact_numbers(client, numbers)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<client_id>/addresses')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientAddresses(Resource):
    @api.response(200, 'Address successfully created')
    @api.doc('create new address')
    @api.expect([_update_client_address], validate=True)
    def put(self, client_id):
        """ Creates new Address """
        addresses = request.json
        client, error_response = _handle_get_client(client_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        return update_client_addresses(client, addresses)

    @api.doc('get client addresses')
    @api.marshal_list_with(_client_address)
    def get(self, client_id):
        client, error_response = _handle_get_client(client_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_addresses(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200


@api.route('/<client_id>/communications')
class ClientCommunications(Resource):
    @api.marshal_list_with(_communication, envelope='data')
    @api.param('_dt', 'Comma separated date fields to be filtered')
    @api.param('_from', 'Start date of communications to query (YYYY-MM-DD)')
    @api.param('_to', 'End date of communications to query (YYYY-MM-DD)')
    @api.param('type', "Default is 'all'. Options are 'call', 'voicemail', or 'sms'")
    def get(self, client_id):
        """ Get all forms of communication for given client """
        client, error_response = _handle_get_client(client_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            filter = filter_request_parse(request)
            comm_types_set = parse_communication_types(request)

            date_range_filter(filter)

            date_filter_fields = filter.get('dt_fields', [])
            result = get_communication_records(filter, comm_types_set, clients=client, date_filter_fields=date_filter_fields)

            return sorted(result, key=lambda record: record.receive_date, reverse=True)


@api.route('/<client_id>/communications/<communication_id>/file')
class ClientCommunicationsFile(Resource):
    @api.doc('Get communications audio file')
    def get(self, client_id, communication_id):
        """ Get voice communication file url """
        client, error_response = _handle_get_client(client_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)

        voice_communication = get_client_voice_communication(client, communication_id)
        if not voice_communication:
            api.abort(404, message='Voice communication not found', success=False)
        else:
            expiration_seconds = 3600
            file_url = create_presigned_url(voice_communication, expiration=expiration_seconds)
            response_object = {
                'success': True,
                'message': f'File URL will expire in {expiration_seconds / 60} minutes.',
                'file_url': file_url
            }
            return response_object, 200


@api.route('/<public_id>/credit-report/debts')
@api.param('public_id', 'The client Identifier')
@api.response(404, 'client or credit report account does not exist')
class ClientCreditReportDebts(Resource):
    @api.doc('fetch credit report data')
    def put(self, public_id):
        """ Update Credit Report Data"""
        client, error_response = _handle_get_client(public_id, ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        credit_account, error_response = _handle_get_credit_report(client)
        if not credit_account:
            api.abort(404, **error_response)

        exists, error_response = check_existing_scrape_task(credit_account)
        if exists:
            api.aport(409, **error_response)

        resp = scrape_credit_report(credit_account, 'Capture credit report debts for Client')

        return resp, 200

    @api.doc('view credit report data')
    @api.marshal_list_with(_credit_report_debt, envelope='data')
    def get(self, public_id):
        """ View Credit Report Data """
        lead, error_response = _handle_get_client(public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        credit_account, error_response = _handle_get_credit_report(lead)
        if not credit_account:
            api.abort(404, **error_response)

        data = get_report_data(credit_account)
        return data, 200

@api.route('/<public_id>/credit-report/account')
@api.param('public_id', 'The CoClient public ID')
class CreateCreditReportAccount(Resource):
    @api.doc('Create credit report account for CoClient. This is Step #1 in process.')
    @api.expect(_new_credit_report_account, validate=True)
    def post(self, public_id):
        request_data = request.json

        coclient, error_response = _handle_get_client(public_id, ClientType.coclient)
        if not coclient:
            api.abort(404, **error_response)

        try:
            app.logger.info('Received request to signup CoClient for a Credit Report Account.')
            creport_acc = creport_account_signup(request_data, coclient, CustomerType.COCLIENT)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': 'Cannot sign up for new Credit Account due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': 'Cannot sign up for new Credit Account due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': f'Successfully created credit report account with {creport_acc.provider}',
            'public_id': creport_acc.public_id
        }        
        return response_object, 201

@api.route('/<coclient_public_id>/credit-report/account/<public_id>')
@api.param('coclient_public_id', 'The CoClient Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class UpdateCreditReportAccount(Resource):
    @api.doc('Update credit report account. This is step #2, and #4 in the process.')
    @api.expect(_update_credit_report_account, validate=True)
    def put(self, coclient_public_id, public_id):
        """ Update Credit Report Account """
        coclient, error_response = _handle_get_client(coclient_public_id, ClientType.coclient)
        if not coclient:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(coclient)
        if not account:
            return error_response
        
        request_data = request.json        
        relevant_data = None
        
        if 'security_question_id' in request_data:
            relevant_data = {
                'security_question_id': request_data['security_question_id'],
                'security_question_answer': request_data['security_question_answer'],
                'ssn': request_data['ssn']
            }
        else:
            relevant_data = request_data
            
        relevant_data['ip_address'] = request.remote_addr
        relevant_data['terms_confirmed'] = True
        
        try:
            app.logger.info(f"Received request to update Credit Report account for CoClient with ID: {coclient_public_id}")
            update_credit_report_account(account, relevant_data)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to update CoClient Credit Report Account, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot update CoClient Credit Report Account due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot update CoClient Credit Report Account due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500
        

        response_object = {
            'success': True,
            'message': 'Successfully updated credit report account for this CoClient'
        }
        return response_object, 200

@api.route('/<coclient_public_id>/credit-report/account/<credit_account_public_id>/security-questions')
@api.param('coclient_public_id', 'The CoClient pubic ID')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CreditReportAccountSecurityQuestions(Resource):
    @api.doc('Get credit report account security questions. This is step #3 in process.')
    def get(self, coclient_public_id, credit_account_public_id):
        """ Get Available Security Questions"""
        coclient, error_response = _handle_get_client(coclient_public_id, ClientType.coclient)
        if not coclient:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(coclient)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to get Credit Account Security Questions for a CoClient.')
            questions = get_security_questions(account)
        
        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get CoClient credit account security questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get CoClient credit account security questions due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        return questions, 200

@api.route('/<coclient_public_id>/credit-report/account/<public_id>/verification-questions')
@api.param('coclient_public_id', 'The CoClient Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class CreditReporAccounttVerification(Resource):
    @api.doc('get verification questions. Step #5 in process.')
    def get(self, coclient_public_id, public_id):
        """ Get Account Verification Questions """
        coclient, error_response = _handle_get_client(coclient_public_id, ClientType.coclient)
        if not coclient:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(coclient)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to get CoClient Credit Account ID Verification Questions.')
            questions = get_verification_questions(account)
        
        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to get CoClient verification questions, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get CoClient verification questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get CoClient verification questions due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        return questions, 200

    @api.doc('Submit answers to verification questions. Step #6 in process.')
    @api.expect(_credit_account_verification_answers, validate=False)
    def put(self, coclient_public_id, public_id):
        """ Submit Account Verification Answers """
        coclient, error_response = _handle_get_client(coclient_public_id, ClientType.coclient)
        if not coclient:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(coclient)
        if not account:
            return error_response

        data = request.json

        try:
            app.logger.info('Received request to answer CoClient Credit Account Verification Questions.')
            answer_verification_questions(account, data)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to submit CoClient verification questions, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot submit CoClient verification questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot submit CoClient verification questions due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': 'Successfully submitted verification answers for this CoClient'
        }
        return response_object, 200

@api.route('/<coclient_public_id>/credit-report/account/<credit_account_public_id>/complete')
@api.param('coclient_public_id', 'The CoClient public ID')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CompleteCreditReportAccount(Resource):
    @api.doc('Complete credit report account signup. Step #7 and final step in process.')
    def put(self, coclient_public_id, credit_account_public_id):
        """ Complete Credit Report Account Sign Up"""
        coclient, error_response = _handle_get_client(coclient_public_id, ClientType.coclient)
        if not coclient:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(coclient)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to complete CoClient Credit Report account signup.')
            complete_signup(account)

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot complete CoClient credit account signup due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot complete CoClient credit account signup due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': 'Successfully completed credit account signup for this CoClient'
        }
        return response_object, 200

@api.route('/<coclient_public_id>/credit-report/account/pull')
@api.param('coclient_public_id', 'CoClient public ID')
@api.response(404, 'CoClient not found')
class CandidateToLead(Resource):
    @api.doc('Pull Credit Report for a CoClient')
    def get(self, coclient_public_id):
        """ Pull Credit Report for CoClient and Import Debts """
        coclient, error_response = _handle_get_client(coclient_public_id, ClientType.coclient)
        if not coclient:
            api.abort(404, **error_response)

        credit_report_account = coclient.credit_report_account
        if not credit_report_account:
            api.abort(404, "No credit report account associated with CoClient. Create Credit Report Account first.")

        app.logger.info("Received request to pull Credit Report for CoClient")
        pull_credit_report(credit_report_account)

        return {"success": True, "message": "Successfully created job to pull Credit Report and import Debts. Check for new Debts in a few minutes."}, 200


@api.route('/<public_id>/service-schedule')
@api.param('public_id', 'Client public ID')
@api.response(404, 'Client not found')
class ClientSvcSchedule(Resource):
    @api.doc('Gets service schedule for a Client')
    @token_required
    def get(self, public_id):
        """ Gets the Service Schedule for a Client """
        client, error_response = _handle_get_client(public_id, ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        app.logger.info("Received request to get Service Schedule for Client")
        svc_sched = get_svc_schedule(client)

        return svc_sched, 200

    @api.doc('Creates the Service Schedule for a Client')
    @token_required
    def post(self, public_id):
        """ Creates the Service Schedule for a Client """
        client, error_response = _handle_get_client(public_id, ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        app.logger.info("Received request to create the Service Schedule for Client")
        svc_sched = create_svc_schedule(client)

        response_object = {
            'success': True,
            'message': f'Successfully created initial Service Schedule for this Client'
        }        
        return response_object, 201

    @api.doc('Updates the Service Schedule for a Client')
    @token_required
    def put(self, public_id):
        """ Updates the Service Schedule for a Client """
        client, error_response = _handle_get_client(public_id, ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        schedule_items = request.json

        try:
            app.logger.info("Received request to updated the Service Schedule for this Client")
            result = update_svc_schedule(client, schedule_items)

        except BadRequestError as e:
            api.abort(400, message='Error updating Service Schedule for client, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error updating Service Schedule for client, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed updating Service Schedule for Client with ID {client_public_id}', success=False)    

        return result, 200

## used for client actions that doesn't require plan change (fee)
## CHANGE DRAFT DATE, CHANGE RECUR DAY, SKIP PAYMENT,
## ADD EFT, REINSTATE AND REFUND 
@api.route('/<client_id>/contract/revision')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientPaymentScheduleRevision(Resource):
    
    @token_required
    @api.doc('revises payment schedule')
    def put(self, client_id):
        """ Revises client payment schedule""" 
        client = get_client(public_id=client_id, client_type=CLIENT) 
        if not client:
            api.abort(404, "Client not found")
        else:
            try:
                user = get_request_user()
                result = contract_open_revision(user, client, request.json)
                return result
            except Exception as err:
                api.abort(500, "{}".format(str(err)))

## RE-INSTATE IS A SPECIAL ACTION
@api.route('/<client_id>/reinstate')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientReinstate(Resource):

    @token_required
    @api.doc('revises payment schedule')
    def put(self, client_id):
        """ Reinstate a client"""
        client = get_client(public_id=client_id, client_type=CLIENT)
        if not client:
            api.abort(404, "Client not found")
        else:
            try:
                user = get_request_user()
                result = contract_reinstate(user, client, request.json) 
                return result
            except Exception as err:
                api.abort(500, "{}".format(str(err)))

