from flask import request
from flask_restplus import Resource

from app.main.controller import _handle_get_client, _handle_get_credit_report, _convert_payload_datetime_values
from app.main.model.client import ClientType
from app.main.seed import DATAX_ERROR_CODES_MANAGER_OVERRIDABLE, DATAX_ERROR_CODES_SALES_OVERRIDABLE
from app.main.service.bank_account_service import create_bank_account
from app.main.service.client_service import get_all_clients, save_new_client, get_client, get_client_income_sources, \
    update_client_income_sources, get_client_monthly_expenses, update_client_monthly_expenses, get_client_employments, \
    update_client_employments, update_client, client_filter, get_client_contact_numbers, update_client_contact_numbers, \
    get_client_addresses, update_client_addresses, get_co_client, update_co_client 
from app.main.service.debt_service import get_report_data, check_existing_scrape_task, scrape_credit_report, add_credit_report_data, delete_debts, \
    push_debts, update_debt
from app.main.service.debt_payment_service import fetch_payment_contract, update_payment_contract
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
_update_lead_address = ClientDto.update_client_address
_co_client = LeadDto.co_client

LEAD = ClientType.lead


@api.route('/')
class LeadList(Resource):
    @api.doc('list_of_clients')
    @api.marshal_list_with(_lead, envelope='data')
    def get(self):
        """ List all clients """
        clients = get_all_clients(client_type=LEAD)
        return clients

    @api.response(201, 'Client successfully created')
    @api.doc('create new client')
    @api.expect(_lead, validate=True)
    def post(self):
        """ Creates new Client """
        data = request.json
        return save_new_client(data=data, client_type=LEAD)


@api.route('/filter')
class LeadFilter(Resource):
    @api.doc('Leads filter with pagination info')
    @api.marshal_with(_lead_pagination)
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
    def get(self, public_id):
        """ Get client with provided identifier"""
        client = get_client(public_id, client_type=LEAD)
        if not client:
            api.abort(404)
        else:
            return client

    @api.doc('update lead')
    #@api.expect(_update_lead, validate=True)
    def put(self, public_id):
        """ Update lead with provided identifier"""
        lead = get_client(public_id, client_type=LEAD)
        if not lead:
            api.abort(404)
        else:
            data = request.json
            _convert_payload_datetime_values(data, 'dob')
            return update_client(lead, data, client_type=LEAD)


@api.route('/<lead_id>/income-sources')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class LeadIncomeSources(Resource):
    @api.doc('get lead income sources')
    @api.marshal_list_with(_lead_income)
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
    def put(self, lead_id):
        """ Creates new Address """
        addresses = request.json
        lead, error_response = _handle_get_client(lead_id, client_type=LEAD)
        if not lead:
            api.abort(404, **error_response)
        return update_client_addresses(lead, addresses)

    @api.doc('get candidate addresses')
    @api.marshal_list_with(_lead_address)
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

@api.route('/<lead_id>/monthly-expenses')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Lead not found')
class ClientMonthlyExpenses(Resource):
    @api.doc('get lead monthly expenses')
    @api.marshal_list_with(_lead_monthly_expense)
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


def _get_codes_for_current_user():
    # TODO: accept a query param for 'override' which will persist the banking information regardless of failure
    # TODO: from the datax service. This 'override' should only be allowed by an ADMIN though
    is_admin = True
    if is_admin:
        return DATAX_ERROR_CODES_MANAGER_OVERRIDABLE
    else:
        return DATAX_ERROR_CODES_SALES_OVERRIDABLE


@api.route('/<public_id>/credit-report/debts')
@api.param('public_id', 'The lead Identifier')
@api.response(404, 'lead or credit report account does not exist')
class LeadCreditReportDebts(Resource):
    @api.doc('fetch credit report data')
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

        resp = scrape_credit_report(credit_account)
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
    
    @api.doc('add credit report data')
    @api.expect([_credit_report_debt], validate=True)
    def post(self, public_id):
        """ add Credit Report Data"""
        lead, error_response = _handle_get_client(public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        credit_account, error_response = _handle_get_credit_report(lead)
        if not credit_account:
            api.abort(404, **error_response)

        data = request.json
        resp = add_credit_report_data(data, credit_account)
        return resp, 200

    @api.doc('delete debts')
    def delete(self, public_id):
        """Delete Debts"""
        request_data = request.json
        delete_debts(request_data.get('ids'))
        return dict(success=True), 200

@api.route('/<public_id>/credit-report/push-debts')
@api.param('public_id', 'The lead Identifier')
@api.response(404, 'lead or credit report account does not exist')
class LeadCreditReportPushDebts(Resource):
    @api.doc('fetch credit report data')
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
    def put(self, public_id):
        """Push Debts"""
        request_data = request.json
        update_debt(request_data.get('data')['debt_data'])
        return dict(success=True), 200

@api.route('/<lead_id>/payment/bank_account')
@api.param('lead_id', 'Lead public identifier')
#@api.param('override', 'Override use of invalid/failing bank information')
@api.response(404, 'Client not found')
class LeadBankAccount(Resource):
    @api.doc('create payment information')
    @api.expect(_new_bank_account, validate=True)
    def post(self, lead_id):
        """ Create/Update Payment Information """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            #override_arg = request.args.get('override')
            #override = True if override_arg.lower() == 'true' else False
            override = False

            overridable_codes = _get_codes_for_current_user()
            result, error = create_bank_account(client, request.json, override=override,
                                                overridable_codes=overridable_codes)
            if error:
                api.abort(500, **error)
            else:
                return result, 200


@api.route('/<lead_id>/payment/plan')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadPaymentPlan(Resource):
    @api.doc('fetch payment plan')
    def get(self, lead_id):
        """ Fetch payment plan for the client """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            try:
                contract = fetch_payment_contract(client) 
                return contract
            except Exception:
                api.abort(500, "Internal Server Error")

    @api.doc('save payment plan')
    def post(self, lead_id):
        """ Save payment plan for the client """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            try:
                # update and fetch the latest contract
                update_payment_contract(client, request.json)
                contract = fetch_payment_contract(client)
                return contract

            except Exception:
                api.abort(500, "Internal Server Error")

@api.route('/<lead_id>/coclient')
@api.param('lead_id', 'Lead public identifier')
@api.response(404, 'Client not found')
class LeadCoClient(Resource):
    @api.doc('fetch co-client for the account')
    @api.marshal_with(_co_client)
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
