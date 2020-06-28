from flask import request
from flask_restplus import Resource, marshal
from werkzeug.exceptions import NotFound

from app.main.core.errors import NotFoundError
from app.main.service.config_service import (get_contact_number_types, get_income_types, get_expense_types,
                                             get_all_candidates_dispositions, get_all_clients_dispositions, get_all_docproc_types,
                                             get_registered_pbx_numbers, register_pbx_number, get_registered_pbx_number_records,
                                             update_pbx_number)
from app.main.util.decorator import token_required, enforce_rac_required_roles

from ..util.dto import ConfigDto, CandidateDto, ClientDto, AuthDto
from app.main.core.rac import RACMgr, RACRoles

api = ConfigDto.api
_income_types = ConfigDto.income_types
_expense_types = ConfigDto.expense_types
_contact_number_types = ConfigDto.contact_number_types
_disposition = ConfigDto.disposition
_candidate_dispositions = CandidateDto.candidate_dispositions
_client_dispositions = ClientDto.client_dispositions
_rac_roles = AuthDto.rac_roles
_docproc_types = ConfigDto.docproc_types
_pbx_number = ConfigDto.pbx_number
_new_pbx_number = ConfigDto.new_pbx_number
_update_pbx_number = ConfigDto.update_pbx_number


@api.route('/docproc-types')
class DocprocTypes(Resource):
    @api.doc('Get known Doc Process Types')
    @api.marshal_list_with(_docproc_types, envelope='data')
    def get(self):
        """ Get all Doc process Types """
        try:
            types = get_all_docproc_types()
        except NotFoundError as e:
            api.abort(404, message='Error getting Doc Process types, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed get Doc Process types. Please report this issue.', success=False)    
        
        return types, 200


@api.route('/rac-roles')
class RacRoles(Resource):
    @api.doc('Get RAC roles')
    @api.marshal_list_with(_rac_roles, envelope='data')
    def get(self):
        """ Get all Contact Number Types """
        try:
            roles = RACMgr.get_all_roles()
        except NotFoundError as e:
            api.abort(404, message='Error getting RAC Roles, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed get RAC Roles. Please report this issue.', success=False)    
        
        return roles, 200
            

@api.route('/contact-number-types')
class ContactNumberTypesList(Resource):
    @api.doc('get contact number types')
    @api.marshal_list_with(_contact_number_types, envelope='data')
    def get(self):
        """ Get all Contact Number Types """
        types = get_contact_number_types()
        return types, 200


@api.route('/income-types')
class IncomeTypesList(Resource):
    @api.doc('get income types')
    @api.marshal_list_with(_income_types, envelope='data')
    def get(self):
        """ Get all Income Types """
        types = get_income_types()
        return types, 200


@api.route('/expense-types')
class ExpenseTypesList(Resource):
    @api.doc('get expense types')
    @api.marshal_list_with(_expense_types, envelope='data')
    def get(self):
        """ Get all Expense types """
        types = get_expense_types()
        return types, 200


@api.route('/candidate-dispositions')
class CandidateDispositionsList(Resource):
    @api.doc('list_of_candidate_dispositions')
    @api.marshal_list_with(_candidate_dispositions, envelope='data')
    def get(self):
        """ List all candidate dispositions"""
        candidate_disposiitions = get_all_candidates_dispositions()
        return candidate_disposiitions


@api.route('/client-dispositions')
class ClientDispositionsList(Resource):
    @api.doc('list_of_client_dispositions')
    @api.marshal_list_with(_client_dispositions, envelope='data')
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def get(self):
        """ List all client dispositions"""
        client_disposiitions = get_all_clients_dispositions()
        return client_disposiitions


@api.route('/pbx-number')
class PBXNumberResource(Resource):
    @api.param('enabled', 'Retrieve PBX Numbers based on whether or not enabled. Default: true')
    @api.marshal_list_with(_pbx_number, envelope='data')
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def get(self):
        enabled = request.args.get('enabled', True)
        return get_registered_pbx_number_records(enabled=enabled)

    @api.response(201, 'PBX Number successfully created.')
    @api.doc('Define a PBX Number for CRM system')
    @api.expect(_new_pbx_number, validate=True)
    @api.marshal_with(_pbx_number)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def post(self):
        data = request.json

        try:
            return register_pbx_number(marshal(data, _new_pbx_number))
        except Exception as e:
            api.abort(500, message=f'Failed to register new PBX Number. Error: {e}', success=False)


@api.route('/pbx-number/<pbx_number_public_id>')
class PBXNumberPatchResource(Resource):
    @api.response(200, 'PBX Number successfully updated.')
    @api.doc('Update a PBX Number for CRM system')
    @api.expect(_update_pbx_number, validate=True)
    @api.marshal_with(_pbx_number)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def patch(self, pbx_number_public_id):
        data = request.json

        try:
            return update_pbx_number(pbx_number_public_id, marshal(data, _update_pbx_number))
        except NotFound:
            api.abort(404, message=f'PBX Number with {pbx_number_public_id} does not exist', success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to register new PBX Number. Error: {e}', success=False)
