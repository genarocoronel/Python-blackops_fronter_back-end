from flask_restplus import Resource

from app.main.service.config_service import get_contact_number_types, get_income_types, get_expense_types, \
    get_all_candidates_dispositions, get_all_clients_dispositions

from ..util.dto import ConfigDto, CandidateDto, ClientDto

api = ConfigDto.api
_income_types = ConfigDto.income_types
_expense_types = ConfigDto.expense_types
_contact_number_types = ConfigDto.contact_number_types
_disposition = ConfigDto.disposition
_candidate_dispositions = CandidateDto.candidate_dispositions
_client_dispositions = ClientDto.client_dispositions


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
    def get(self):
        """ List all client dispositions"""
        client_disposiitions = get_all_clients_dispositions()
        return client_disposiitions
