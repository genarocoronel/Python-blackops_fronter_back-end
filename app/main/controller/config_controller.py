from flask import request
from flask_restplus import Resource, marshal
from werkzeug.exceptions import NotFound

from app.main.core.errors import NotFoundError
from app.main.service.config_service import (get_contact_number_types, get_income_types, get_expense_types,
                                             get_all_candidates_dispositions, get_all_clients_dispositions, get_all_docproc_types,
                                             register_pbx_number, get_registered_pbx_number_records,
                                             update_pbx_number, get_pbx_systems, register_pbx_system, delete_pbx_system,
                                             map_number_to_pbx_system, update_pbx_system)
from app.main.util.decorator import token_required, enforce_rac_required_roles, user_has_permission

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
_pbx_system = ConfigDto.pbx_system
_new_pbx_system = ConfigDto.new_pbx_system
_update_pbx_system = ConfigDto.update_pbx_system
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
    @user_has_permission('clients.view')
    def get(self):
        """ List all client dispositions"""
        client_disposiitions = get_all_clients_dispositions()
        return client_disposiitions


@api.route('/pbx-systems')
class PBXSystemListResource(Resource):
    @api.param('enabled', 'Retrieve PBX Systems based on whether or not enabled. Default: true. Options: true, false, all')
    @api.marshal_list_with(_pbx_system, envelope='data')
    @token_required
    @user_has_permission('clients.view')
    def get(self):
        enabled = request.args.get('enabled', True)
        return get_pbx_systems(enabled)

    @api.response(201, 'PBX System successfully created.')
    @api.doc('Define a PBX System for CRM system')
    @api.expect(_new_pbx_system, validate=True)
    @api.marshal_with(_pbx_system)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def post(self):
        data = request.json

        try:
            return register_pbx_system(marshal(data, _new_pbx_system))
        except Exception as e:
            api.abort(500, message=f'Failed to register new PBX System. Error: {e}', success=False)


@api.route('/pbx-systems/<pbx_system_public_id>')
@api.param('pbx_system_public_id', 'PBX System Public Identifier')
class PBXSystemResource(Resource):
    @api.response(200, 'PBX System successfully updated.')
    @api.doc('Update a PBX System in CRM system')
    @api.expect(_update_pbx_system, validate=True)
    @api.marshal_with(_pbx_system)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def put(self, pbx_system_public_id):
        try:
            return update_pbx_system(pbx_system_public_id, marshal(request.json, _update_pbx_system))
        except NotFound:
            api.abort(404, message='PBX System does not exist', success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to update PBX System. Error: {e}', success=False)

    @api.response(200, 'PBX System successfully deleted.')
    @api.doc('Delete a PBX System from CRM system')
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def delete(self, pbx_system_public_id):
        try:
            delete_pbx_system(pbx_system_public_id)
            return dict(message='Successfully deleted PBX System', success=True), 200
        except NotFound:
            api.abort(404, message='PBX System does not exist', success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to delete PBX System. Error: {e}', success=False)


@api.route('/pbx-systems/<pbx_system_public_id>/pbx-number/<pbx_number_public_id>')
@api.param('pbx_system_public_id', 'PBX System Public Identifier')
@api.param('pbx_number_public_id', 'PBX Number Public Identifier')
class PBXSystemNumberResource(Resource):
    def put(self, pbx_system_public_id, pbx_number_public_id):
        try:
            map_number_to_pbx_system(pbx_system_public_id, pbx_number_public_id)
            return dict(message='Successfully mapped number to PBX system', success=True)
        except NotFound:
            api.abort(404, 'PBX system or number does not exist', success=False)
        except Exception as e:
            api.abort(500, f'Failed to map number to PBX system. Error: {e}', success=False)


@api.route('/pbx-number')
class PBXNumberResource(Resource):
    @api.param('enabled', 'Retrieve PBX Numbers based on whether or not enabled. Default: true. Options: true, false, all')
    @api.marshal_list_with(_pbx_number, envelope='data')
    @token_required
    @user_has_permission('clients.view')
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
