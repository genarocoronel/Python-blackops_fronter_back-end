from flask import request
from flask_restplus import Resource

from app.main.controller import _handle_get_client, _handle_get_credit_report, _convert_payload_datetime_values
from app.main.model.client import ClientType
from app.main.seed import DATAX_ERROR_CODES_MANAGER_OVERRIDABLE, DATAX_ERROR_CODES_SALES_OVERRIDABLE
from app.main.service.bank_account_service import create_bank_account
from app.main.service.client_service import get_all_clients, save_new_client, get_client, get_client_employments, update_client_employments
from app.main.service.credit_report_account_service import save_changes
from app.main.service.debt_service import get_report_data, check_existing_scrape_task
from ..util.dto import LeadDto, ClientDto

api = LeadDto.api
_lead = LeadDto.lead
_new_bank_account = ClientDto.new_bank_account
_bank_account = ClientDto.bank_account
_credit_report_debt = LeadDto.credit_report_debt
_lead_employment = ClientDto.client_employment
_update_lead_employment = ClientDto.update_client_employment

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
    @api.expect([_update_lead_employment], validate=True)
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
            api.aport(409, **error_response)

        task = credit_account.launch_spider(
            'capture',
            'Capture credit report debts for lead',  # TODO: allow passing custom message for task execution
        )
        save_changes(task)

        resp = {
            'message': 'Spider queued',
            'task_id': task.id
        }
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


@api.route('/<lead_id>/bank-account')
@api.param('lead_id', 'Lead public identifier')
@api.param('override', 'Override use of invalid/failing bank information')
@api.response(404, 'Client not found')
class LeadBankAccount(Resource):
    @api.doc('create bank account')
    @api.expect(_new_bank_account, validate=True)
    def post(self, lead_id):
        """ Create Bank Account """
        client = get_client(public_id=lead_id, client_type=ClientType.lead)
        if not client:
            api.abort(404)
        else:
            override_arg = request.args.get('override')
            override = True if override_arg.lower() == 'true' else False

            overridable_codes = _get_codes_for_current_user()
            result, error = create_bank_account(client, request.json, override=override,
                                                overridable_codes=overridable_codes)
            if error:
                api.abort(500, **error)
            else:
                return None, 201
