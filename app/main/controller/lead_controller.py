from flask import current_app as app
from flask import request
from flask_restplus import Resource

from app.main.controller import _handle_get_client, _handle_get_credit_report, _convert_payload_datetime_values, _parse_datetime_values
from app.main.core.errors import (BadRequestError, ServiceProviderError, ServiceProviderLockedError)
from app.main.util.decorator import (token_required, user_has_permission)
from app.main.core.types import CustomerType
from app.main.model.client import ClientType
from app.main.service.bank_account_service import create_bank_account
from app.main.service.client_service import get_all_clients, save_new_client, get_client, get_client_income_sources, \
    update_client_income_sources, get_client_monthly_expenses, update_client_monthly_expenses, get_client_employments, \
    update_client_employments, update_client, client_filter, get_client_contact_numbers, update_client_contact_numbers, \
    get_client_addresses, update_client_addresses, get_co_client, update_co_client, get_client_checklist, update_client_checklist, \
    update_notification_pref, fetch_client_combined_debts, assign_salesrep
from app.main.service.communication_service import parse_communication_types, date_range_filter, get_client_voice_communication, \
    create_presigned_url, get_sales_and_service_communication_records
from app.main.service.credit_report_account_service import (creport_account_signup, update_credit_report_account,
                                                            create_manual_creport_account,
                                                            get_verification_questions, answer_verification_questions,
                                                            get_security_questions, complete_signup, pull_credit_report,
                                                            get_account_credentials)
from app.main.service.debt_payment_service import fetch_payment_contract, update_payment_contract, payment_contract_action, \
    payment_contract_req4approve, fetch_amendment_plan, update_amendment_plan, \
    fetch_payment_schedule, update_payment_schedule
from app.main.service.debt_service import check_existing_scrape_task, scrape_credit_report, add_credit_report_data, delete_debts, \
    push_debts, update_debt
from app.main.service.user_service import get_request_user, get_a_user
from app.main.service.docproc_service import get_docs_for_client, create_doc_manual, get_doc_by_pubid, update_doc
from app.main.service.audit_service import get_last_audit_item
from app.main.model.audit import Auditable
from ..util.dto import LeadDto, ClientDto
from ..util.parsers import filter_request_parse

api = LeadDto.api
_lead = LeadDto.lead
_lead_pagination = LeadDto.lead_pagination
_update_lead = LeadDto.update_lead
_new_bank_account = ClientDto.new_bank_account
_bank_account = ClientDto.bank_account
_credit_report_debt = LeadDto.credit_report_debt
_lead_employment = ClientDto.client_employment
_update_lead_employment = ClientDto.update_client_employment
_lead_income = ClientDto.client_income
_update_lead_income = ClientDto.update_client_income
_lead_monthly_expense = ClientDto.client_monthly_expense
_update_lead_monthly_expense = ClientDto.update_client_monthly_expense
_contact_number = ClientDto.contact_number
_update_contact_number = ClientDto.update_contact_number
_lead_address = ClientDto.client_address
_communication = ClientDto.communication
_update_lead_address = ClientDto.update_client_address
_co_client = LeadDto.co_client
_new_credit_report_account = LeadDto.new_credit_report_account
_update_credit_report_account = LeadDto.update_credit_report_account
_credit_account_verification_answers = LeadDto.account_verification_answers
_last_action = ClientDto.last_action
_doc = LeadDto.doc
_doc_create = LeadDto.doc_create
_last_action = LeadDto.last_action

LEAD = ClientType.lead


@api.route('/')
class LeadList(Resource):
    @api.doc('list_of_clients')
    @api.marshal_list_with(_lead, envelope='data')
    @token_required
    @user_has_permission('leads.view')
    def get(self):
        """ List all clients """
        clients = get_all_clients(client_type=LEAD)
        return clients

    @api.response(201, 'Client successfully created')
    @api.doc('create new client')
    @api.expect(_lead, validate=True)
    @token_required
    @user_has_permission('leads.create')
    def post(self):
        """ Creates new Client """
        data = request.json
        return save_new_client(data=data, client_type=LEAD)


@api.route('/filter')
class LeadFilter(Resource):
    @api.doc('Leads filter with pagination info')
    @api.marshal_with(_lead_pagination)
    @token_required
    @user_has_permission('leads.view')
    def get(self):
        #filter args
        fargs = filter_request_parse(request)
        result =  client_filter(client_type=LEAD, **fargs)
        return result, 200


@api.route('/new')
class LeadNew(Resource):
    @api.response(201, 'Client successfully created') 
    @api.doc('create a new lead')
    #@api.expect(_lead, validate=True)
    @api.marshal_with(_lead)
    @token_required
    @user_has_permission('leads.create')
    def put(self):
        """Create a new Lead"""    
        data = request.json
        return save_new_client(data=data, client_type=LEAD)


@api.route('/<public_id>')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Client not found')
class Lead(Resource):
    @api.doc('get client')
    @api.marshal_with(_lead)
    @token_required
    @user_has_permission('leads.view')
    def get(self, public_id):
        """ Get client with provided identifier"""
        client = get_client(public_id, client_type=LEAD)
        if not client:
            api.abort(404, "Lead not found")
        else:
            return client

    @api.doc('update lead')
    #@api.expect(_update_lead, validate=True)
    @api.marshal_with(_lead)
    @token_required
    @user_has_permission('leads.update')
    def put(self, public_id):
        """ Update lead with provided identifier"""
        lead = get_client(public_id, client_type=LEAD)
        if not lead:
            api.abort(404, "Lead not found")
        else:
            data = request.json
            try:
                _parse_datetime_values(data, 'dob')
            except Exception as err:
                api.abort(400, "DOB: {}".format(str(err)))

            return update_client(lead, data, client_type=LEAD)


@api.route('/<public_id>/assign/<user_public_id>/')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Lead not found')
class LeadAssignment(Resource):
    @api.doc('Assigns a Lead to a Sales Rep user')
    @token_required
    @user_has_permission('leads.assignment')
    def put(self, public_id, user_public_id):
        """ Assigns a Lead to a Sales Rep user """
        lead = get_client(public_id, client_type=LEAD)
        if not lead:
            api.abort(404, "Lead not found")
        
        asignee = get_a_user(user_public_id)
        if not asignee:
            api.abort(404, message='That Sales Rep could not be found.', success=False)

        try:
            assign_salesrep(lead, asignee.id)

        except Exception as e:
            api.abort(500, message=f'Failed to assign a Sales Rep for this Lead. Error: {e}', success=False)

        response_object = {
            'success': True,
            'message': f'Successfully assigned this Lead to Sales Rep with ID {user_public_id}.',
        }
        return response_object, 200


@api.route('/<lead_id>/income-sources')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class LeadIncomeSources(Resource):
    @api.doc('get lead income sources')
    @api.marshal_list_with(_lead_income)
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_income_sources(lead)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update lead income sources')
    @api.expect([_update_lead_income], validate=True)
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id):
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            numbers = request.json
            result, err_msg = update_client_income_sources(lead, numbers)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<lead_id>/contact_numbers')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class LeadContactNumbers(Resource):
    @api.doc('get lead contact numbers')
    @api.marshal_list_with(_contact_number)
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_contact_numbers(lead)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update lead contact numbers')
    @api.expect([_update_contact_number], validate=True)
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id):
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            numbers = request.json
            result, err_msg = update_client_contact_numbers(lead, numbers)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<lead_id>/addresses')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class LeadAddresses(Resource):
    @api.response(200, 'Address successfully created')
    @api.doc('create new address')
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id):
        """ Creates new Address """
        addresses = request.json
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        return update_client_addresses(lead, addresses)

    @api.doc('get Lead addresses')
    @api.marshal_list_with(_lead_address)
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_addresses(lead)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200


@api.route('/<lead_id>/communications')
class LeadCommunications(Resource):
    @api.marshal_list_with(_communication, envelope='data')
    @api.param('_dt', 'Comma separated date fields to be filtered')
    @api.param('_from', 'Start date of communications to query (YYYY-MM-DD)')
    @api.param('_to', 'End date of communications to query (YYYY-MM-DD)')
    @api.param('type', "Default is 'all'. Options are 'call', 'voicemail', or 'sms'")
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        """ Get all forms of communication for given client """
        try:
            lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
            if not lead:
                api.abort(404, **error_response)
            else:
                filter = filter_request_parse(request)
                comm_types_set = parse_communication_types(request)

                date_range_filter(filter)

                date_filter_fields = filter.get('dt_fields', [])
                result = get_sales_and_service_communication_records(filter, comm_types_set, clients=lead, date_filter_fields=date_filter_fields)

                return sorted(result, key=lambda record: record.receive_date, reverse=True)
        except Exception as e:
            api.abort(500, message=f'Failed to retrieve communication records for lead. Error: {e}', success=False)


@api.route('/<lead_id>/communications/<communication_id>/file')
class LeadCommunicationsFile(Resource):
    @api.doc('Get communications audio file')
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id, communication_id):
        """ Get voice communication file url """
        try:
            lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
            if not lead:
                api.abort(404, **error_response)

            voice_communication = get_client_voice_communication(lead, communication_id)
            if not voice_communication:
                api.abort(404, message='Voice communication not found')
            else:
                expiration_seconds = app.s3_signed_url_timeout_seconds
                file_url = create_presigned_url(voice_communication, expiration=expiration_seconds)
                response_object = {
                    'success': True,
                    'message': f'File URL will expire in {expiration_seconds / 60} minutes.',
                    'file_url': file_url
                }
                return response_object, 200
        except Exception as e:
            api.abort(500, message=f'Failed to retrieve url for audio file. Error: {e}', success=False)


@api.route('/<lead_id>/monthly-expenses')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class ClientMonthlyExpenses(Resource):
    @api.doc('get lead monthly expenses')
    @api.marshal_list_with(_lead_monthly_expense)
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_monthly_expenses(lead)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update lead monthly expenses')
    @api.expect([_update_lead_monthly_expense], validate=True)
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id):
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            expenses = request.json
            result, err_msg = update_client_monthly_expenses(lead, expenses)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<public_id>/employments')
@api.param('public_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class LeadEmployments(Resource):
    @api.doc('get lead employments')
    @api.marshal_list_with(_lead_employment)
    @token_required
    @user_has_permission('leads.view')
    def get(self, public_id):
        lead, error_response = _handle_get_client(public_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_employments(lead)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update lead employment')
    @token_required
    @user_has_permission('leads.update')
    def put(self, public_id):
        lead, error_response = _handle_get_client(public_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        else:
            employments = request.json
            _convert_payload_datetime_values(employments, 'start_date', 'end_date')

            result, err_msg = update_client_employments(lead, employments)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<public_id>/credit-report/debts')
@api.param('public_id', 'The lead Identifier')
@api.response(404, 'lead or credit report account does not exist')
class LeadCreditReportDebts(Resource):
    @api.doc('fetch credit report data')
    @token_required
    @user_has_permission('leads.debts.view')
    def put(self, public_id):
        """ Fetch Credit Report Data"""
        lead, error_response = _handle_get_client(public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        credit_account, error_response = _handle_get_credit_report(lead)
        if not credit_account:
            api.abort(404, **error_response)

        exists, error_response = check_existing_scrape_task(credit_account)
        if exists:
            api.abort(409, **error_response)

        resp = scrape_credit_report(credit_account, 'Capture credit report debts for Lead')
        return resp, 200

    @api.doc('view credit report data')
    @api.marshal_list_with(_credit_report_debt, envelope='data')
    @token_required
    @user_has_permission('leads.debts.view')
    def get(self, public_id):
        """ View Credit Report Data """
        lead, error_response = _handle_get_client(public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        data = fetch_client_combined_debts(lead)
        return data, 200
    
    @api.doc('add credit report data')
    @api.expect([_credit_report_debt], validate=True)
    @token_required
    @user_has_permission('leads.debts.create')
    def post(self, public_id):
        """ add Credit Report Data"""
        lead, error_response = _handle_get_client(public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        credit_account, error_response = _handle_get_credit_report(lead)
        if not credit_account:
            credit_account = create_manual_creport_account(lead)

        data = request.json
        resp = add_credit_report_data(data, credit_account)
        return resp, 200

    @api.doc('delete debts')
    @token_required
    @user_has_permission('leads.debts.delete')
    def delete(self, public_id):
        """Delete Debts"""
        request_data = request.json
        delete_debts(request_data.get('ids'))
        return dict(success=True), 200

@api.route('/<public_id>/credit-report/account')
@api.param('public_id', 'The Lead public ID')
class CreateCreditReportAccount(Resource):
    @api.doc('Create credit report account for Lead. This is Step #1 in process.')
    @api.expect(_new_credit_report_account, validate=True)
    @token_required
    @user_has_permission('leads.debts.create')
    def post(self, public_id):
        request_data = request.json

        lead, error_response = _handle_get_client(public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        try:
            app.logger.info('Received request to signup Lead for a Credit Report Account.')
            creport_acc = creport_account_signup(request_data, lead, CustomerType.LEAD)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot sign up for new Credit Account due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot sign up for new Credit Account due to a service provider issue, {str(e)}'
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

    
@api.route('/<lead_public_id>/credit-report/account/<public_id>')
@api.param('lead_public_id', 'The Lead Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class UpdateCreditReportAccount(Resource):
    @api.doc('update credit report account. This is step #2, and #4 in the process.')
    @api.expect(_update_credit_report_account, validate=True)
    @token_required
    @user_has_permission('leads.debts.update')
    def put(self, lead_public_id, public_id):
        """ Update Credit Report Account """
        lead, error_response = _handle_get_client(lead_public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(lead)
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
            app.logger.info(f"Received request to update Credit Report account for Lead with ID: {lead_public_id}")
            update_credit_report_account(account, relevant_data)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to update Lead Credit Report Account, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot update Lead Credit Report Account due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot update Lead Credit Report Account due to a service provider issue, {str(e)}'
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
            'message': 'Successfully updated credit report account for this Lead'
        }
        return response_object, 200

@api.route('/<lead_public_id>/credit-report/account/<credit_account_public_id>/security-questions')
@api.param('lead_public_id', 'The Lead pubic ID')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CreditReportAccountSecurityQuestions(Resource):
    @api.doc('get credit report account security questions. This is step #3 in process.')
    @token_required
    @user_has_permission('leads.debts.view')
    def get(self, lead_public_id, credit_account_public_id):
        """ Get Available Security Questions"""
        lead, error_response = _handle_get_client(lead_public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(lead)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to get Credit Account Security Questions for a Lead.')
            questions = get_security_questions(account)
        
        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get Lead credit account security questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get Lead credit account security questions due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        return questions, 200


@api.route('/<lead_public_id>/credit-report/account/<public_id>/verification-questions')
@api.param('lead_public_id', 'The Lead Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class CreditReporAccounttVerification(Resource):
    @api.doc('get verification questions. Step #5 in process.')
    @token_required
    @user_has_permission('leads.debts.view')
    def get(self, lead_public_id, public_id):
        """ Get Account Verification Questions """
        lead, error_response = _handle_get_client(lead_public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(lead)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to get Lead Credit Account ID Verification Questions.')
            questions = get_verification_questions(account)
        
        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to get Lead verification questions, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get Lead verification questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get Lead verification questions due to a service provider issue, {str(e)}'
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
    @token_required
    @user_has_permission('leads.debts.view')
    def put(self, lead_public_id, public_id):
        """ Submit Account Verification Answers """
        lead, error_response = _handle_get_client(lead_public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(lead)
        if not account:
            return error_response

        data = request.json

        try:
            app.logger.info('Received request to answer Lead Credit Account Verification Questions.')
            answer_verification_questions(account, data)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to submit verification questions, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot submit Lead verification questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot submit Lead verification questions due to a service provider issue, {str(e)}'
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
            'message': 'Successfully submitted verification answers for this Lead'
        }
        return response_object, 200


@api.route('/<lead_public_id>/credit-report/account/<credit_account_public_id>/complete')
@api.param('lead_public_id', 'The Lead public ID')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CompleteCreditReportAccount(Resource):
    @api.doc('Complete credit report account signup. Step #7 and final step in process.')
    @token_required
    @user_has_permission('leads.debts.view')
    def put(self, lead_public_id, credit_account_public_id):
        """ Complete Credit Report Account Sign Up"""
        lead, error_response = _handle_get_client(lead_public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(lead)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to complete Lead Credit Report account signup.')
            complete_signup(account)

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot complete Lead credit account signup due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot complete Lead credit account signup due to a service provider issue, {str(e)}'
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
            'message': 'Successfully completed credit account signup for this Lead'
        }
        return response_object, 200


@api.route('/<lead_public_id>/credit-report/account/credentials')
@api.param('candidate_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class LeadCReportCredentials(Resource):
    @api.doc('Get Lead SCredit Acc credentials')
    @token_required
    @user_has_permission('leads.debts.view')
    def get(self, lead_public_id):
        """ Get Lead SCredit Acc credentials """
        lead, error_response = _handle_get_client(lead_public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        if not lead.credit_report_account:
            api.abort(404, 'This Lead does not have a SCredit account')

        credentials_decrypted = get_account_credentials(lead)
        return credentials_decrypted, 200


@api.route('/<lead_public_id>/credit-report/account/pull')
@api.param('lead_public_id', 'Lead public ID')
@api.response(404, 'Lead not found')
class CandidateToLead(Resource):
    @api.doc('Pull Credit Report for a Lead')
    @token_required
    @user_has_permission('leads.debts.view')
    def get(self, lead_public_id):
        """ Pull Credit Report for Lead and Import Debts """
        lead, error_response = _handle_get_client(lead_public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        credit_report_account = lead.credit_report_account
        if not credit_report_account:
            api.abort(404, "No credit report account associated with Lead. Create Credit Report Account first.")

        app.logger.info("Received request to pull Credit Report for Lead")
        pull_credit_report(credit_report_account)

        return {"success": True, "message": "Successfully created job to pull Credit Report and import Debts. Check for new Debts in a few minutes."}, 200


@api.route('/<public_id>/credit-report/push-debts')
@api.param('public_id', 'The lead Identifier')
@api.response(404, 'lead or credit report account does not exist')
class LeadCreditReportPushDebts(Resource):
    @api.doc('Update credit report data')
    @token_required
    @user_has_permission('leads.debts.update')
    def put(self, public_id):
        """Push Debts"""
        request_data = request.json
        push_debts(request_data.get('data')['ids'], request_data.get('data')['push'])
        return dict(success=True), 200


@api.route('/<public_id>/credit-report/update-debt')
@api.param('public_id', 'The lead Identifier')
@api.response(404, 'lead or credit report account does not exist')
class LeadCreditReportUpdateDebt(Resource):
    @api.doc('fetch credit report data')
    @token_required
    @user_has_permission('leads.debts.update')
    def put(self, public_id):
        """Push Debts"""
        request_data = request.json
        update_debt(request_data.get('data')['debt_data'])
        return dict(success=True), 200


@api.route('/<lead_id>/payment/bank_account')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadBankAccount(Resource):
    @api.doc('create payment information')
    @api.expect(_new_bank_account, validate=True)
    @token_required
    @user_has_permission('leads.update')
    def post(self, lead_id):
        """ Create/Update Payment Information """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            result, error = create_bank_account(client, 
                                                request.json)
            if error:
                api.abort(500, **error)
            else:
                return result, 200


@api.route('/<lead_id>/coclient')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadCoClient(Resource):
    @api.doc('fetch co-client for the account')
    @api.marshal_with(_co_client)
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        """ fetch co-client for the lead"""
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            try:
                co_client = get_co_client(client)
                return co_client
            except Exception:
                api.abort(500, "Internal Server Error")

    @api.doc('add co-client')
    @api.marshal_with(_co_client)
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id):
        """Adds co-clien to the lead"""
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            try:
                # update and fetch the latest contract
                co_client = update_co_client(client, request.json)
                return co_client

            except Exception:
                api.abort(500, "Internal Server Error")


@api.route('/<lead_id>/checklist')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadChecklist(Resource):
    @api.doc('fetch checklist for the lead')
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        """ fetch checklist for the lead"""
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, "Lead not found")
        else:
            try:
                checklist = get_client_checklist(client)
                return checklist
            except Exception as err:
                api.abort(500, "{}".format(str(err)))

    @api.doc('update checklist for the lead')
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id):
        """ update checklist for the lead"""
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, "Lead not found")
        else:
            try:
                data = request.json
                checklist = update_client_checklist(client, data)
                return checklist
            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/notification/prefs')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadNotificationPrefs(Resource):
    @api.doc('update notification preferences')
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id):
        """ update notification preferences for the lead"""
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, "Lead not found")
        else:
            try:
                data = request.json
                prefs = update_notification_pref(client, data)
                return prefs
            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/payment/plan')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadPaymentPlan(Resource):
    @api.doc('fetch payment plan')
    @token_required
    @user_has_permission('leads.contract.view')
    def get(self, lead_id):
        """ Fetch payment plan for the client """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            try:
                contract = fetch_payment_contract(client) 
                return contract
            except Exception as err:
                api.abort(500, "{}".format(str(err)))

    @api.doc('save payment plan')
    @token_required
    @user_has_permission('leads.contract.create')
    def post(self, lead_id):
        """ Save payment plan for the client """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, 'Client not found')
        else:
            try:
                # update and fetch the latest contract
                update_payment_contract(client, request.json)
                contract = fetch_payment_contract(client)
                return contract

            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/amendment/<plan_id>')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadAmendmentPlanById(Resource):
    @api.doc('fetch amendment plan')
    @token_required
    @user_has_permission('clients.amendment.view')
    def get(self, lead_id, plan_id):
        """ Fetch amended contract for the client """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, 'Client not found')
        else:
            try:
                contract = fetch_amendment_plan(client, plan_id)
                return contract
            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/amendment/plan')
@api.response(404, 'Client not found')
class LeadAmendmentPlan(Resource):
    @api.doc('fetch amendment plan')
    @token_required
    @user_has_permission('clients.amendment.view')
    def get(self, lead_id):
        """ Fetch amendment plan for the client """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, 'Client not found')
        else:
            try:
                # update and fetch the latest contract
                plan = fetch_amendment_plan(client)
                return plan

            except Exception as err:
                api.abort(500, "{}".format(str(err)))

    @api.doc('save amendment plan')
    @token_required
    @user_has_permission('clients.amendment.update')
    def put(self, lead_id):
        """ Save amendment plan for the client """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, 'Client not found')
        else:
            try:
                # update and fetch the latest contract
                update_amendment_plan(client, request.json)
                plan = fetch_amendment_plan(client)
                return plan

            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/payment/plan/req4approve')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadApprovePlanRequest(Resource):
    @api.doc('request for approval')
    @token_required
    @user_has_permission('clients.amendment.request')
    def post(self, lead_id):
        """ Request for approval"""
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, "Client not found")
        else:
            try:
                user = get_request_user()
                if user is None:
                    api.abort(404, "User not found")
                return payment_contract_req4approve(user, 
                                                    client, 
                                                    request.json)

            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/payment/plan/action')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadActionPlan(Resource):
    @api.doc('sends docusign document')
    @token_required
    @user_has_permission('leads.contract.send')
    def post(self, lead_id):
        """ Sends a docusign document """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, "Client not found")
        else:
            try:
                return payment_contract_action(client)
            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/payment/schedule')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadPaymentSchedule(Resource):
    @api.doc('fetches payment schedule')
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, "Client not found")
        else:
            try:
                schedule = fetch_payment_schedule(client)
                return schedule

            except Exception as err:
                api.abort(500, "{}".format(str(err)))

@api.route('/<lead_id>/payment/schedule/<record_id>')
@api.param('lead_id', 'Lead public identifier')
@api.param('record_id', 'Schedule record identifier')
@api.response(404, 'Client not found')
class LeadPaymentRecord(Resource):
    @api.doc('Updates payment schedule record')
    @token_required
    @user_has_permission('leads.update')
    def put(self, lead_id, record_id):
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, "Client not found")
        else:
            try:
                data = request.json
                result = update_payment_schedule(client, record_id, data)
                return result, 200
            except Exception as err:
                api.abort(500, "{}".format(str(err)))


@api.route('/<lead_id>/docs')
@api.param('lead_id', 'Lead public identifier')
class LeadDocs(Resource):
    @api.doc('Get Lead documents')
    @api.marshal_list_with(_doc)
    @token_required
    @user_has_permission('leads.view')
    def get(self, lead_id):
        """ Get Lead documents """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        docs = get_docs_for_client(client)

        return docs, 200


    @api.doc('Creates a Doc for a Lead')
    @api.expect(_doc_create, validate=True)
    @token_required
    @user_has_permission('leads.view')
    def post(self, lead_id):
        """ Creates a Doc manually """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        request_data = request.json

        try:
            doc = create_doc_manual(request_data, client)

        except BadRequestError as e:
            api.abort(400, message='Error creating doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error creating doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to create Doc', success=False)

        return doc, 200


@api.route('/<lead_id>/last-action')
@api.param('lead_id', 'Lead public identifier')
class LeadLastAction(Resource):
    @api.doc('Get Lead last action')
    @api.marshal_list_with(_last_action)
    @token_required
    def get(self, lead_id):
        """ Get Lead last action """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        last_action = get_last_audit_item(client.public_id, Auditable.LEAD)

        return last_action, 200
