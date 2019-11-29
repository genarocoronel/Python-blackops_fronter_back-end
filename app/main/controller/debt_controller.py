from flask import request
from flask_restplus import Resource
from app.main import db
from ..util.dto import DebtDto, LeadDto
from app.main.model.client import ClientType
from app.main.service.client_service import get_client
from app.main.service.debt_service import *


api = DebtDto.api
_credit_report_data = DebtDto.credit_report_data
_new_report_data = DebtDto.new_report_data


def _handle_get_client(public_id):
    lead = get_client(public_id, client_type=ClientType.lead)
    if not lead:
        error_response = {
                'success': False,
                'message': 'Client not found'
            }
        return None, error_response
    return lead, 200


@api.route('/<client_public_id>')
class CreditReportDebts(Resource):
    @api.doc('view debts for client')
    @api.marshal_list_with(_credit_report_data, envelope='data')
    def get(self, client_public_id):
        """List Debts for Client"""
        lead, error_response = _handle_get_client(client_public_id)
        if not lead:
            api.abort(404, **error_response)
        data = get_report_data(lead.credit_report_account)
        return data, 200

    @api.doc('create debt for client')
    @api.expect(_new_report_data, validate=True)
    def post(self, client_public_id):
        """Create Debt for Client"""
        try:
            lead, error_response = _handle_get_client(client_public_id)
            if not lead:
                api.abort(404, **error_response)
            request_data = request.json

            new_debt = save_new_debt(request_data, lead.credit_report_account)
            response_object = {
                'success': True,
                'message': f'Successfully created debt for client {client_public_id}',
                'public_id': new_debt.public_id
            }
            return response_object, 201
        except Exception as ex:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/<client_public_id>/debt/<debt_public_id>')
class ViewCreditReportDebt(Resource):
    @api.doc('view one debt for client')
    @api.marshal_with(_credit_report_data)
    def get(self, client_public_id,  debt_public_id):
        """View particular debt for Client"""
        lead, error_response = _handle_get_client(client_public_id)
        if not lead:
            api.abort(404, **error_response)
        data = get_report_data(lead.credit_report_account, debt_public_id)
        return data, 200

    @api.doc('update particular debt for client')
    @api.expect(_new_report_data, validate=True)
    def put(self, client_public_id,  debt_public_id):
        """Update particular debt for Client"""
        try:
            lead, error_response = _handle_get_client(client_public_id)
            if not lead:
                api.abort(404, **error_response)
            request_data = request.json

            return update_debt(
                request_data, lead.credit_report_account, debt_public_id)
        except Exception as ex:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500
