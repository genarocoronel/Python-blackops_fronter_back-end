from flask import request
from flask_restplus import Resource

from app.main.service.config_service import get_contact_number_types, get_income_types, get_expense_types, get_dispositions

from ..util.dto import ConfigDto

api = ConfigDto.api
_income_types = ConfigDto.income_types
_expense_types = ConfigDto.expense_types
_contact_number_types = ConfigDto.contact_number_types
_disposition = ConfigDto.disposition


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

@api.route('/dispositions')
class ExpenseTypesList(Resource):
    @api.doc('get dispositions')
    @api.marshal_list_with(_disposition, envelope='data')
    def get(self):
        """ Get all Expense types """
        dispositions = get_dispositions()
        return dispositions, 200