from flask import request
from flask_restplus import Resource

from app.main.model.client import ClientType
from app.main.seed import DATAX_ERROR_CODES_MANAGER_OVERRIDABLE, DATAX_ERROR_CODES_SALES_OVERRIDABLE
from app.main.service.bank_account_service import create_bank_account
from app.main.service.client_service import get_all_clients, save_new_client, get_client, get_client_bank_account
from ..util.dto import LeadDto, ClientDto

api = LeadDto.api
_lead = LeadDto.lead
_new_bank_account = ClientDto.new_bank_account
_bank_account = ClientDto.bank_account

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


def _get_codes_for_current_user():
    # TODO: accept a query param for 'override' which will persist the banking information regardless of failure
    # TODO: from the datax service. This 'override' should only be allowed by an ADMIN though
    is_admin = True
    if is_admin:
        return DATAX_ERROR_CODES_MANAGER_OVERRIDABLE
    else:
        return DATAX_ERROR_CODES_SALES_OVERRIDABLE


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
