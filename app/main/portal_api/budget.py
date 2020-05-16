from flask_restplus import Resource

from app.main.util.portal_dto import BudgetDto
from app.main.util.decorator import portal_token_required
from app.main.service.budget_service import get_all_income_sources, get_all_monthly_expenses

api = BudgetDto.api
_income_source = BudgetDto.income_source
_monthly_expense = BudgetDto.monthly_expense

@api.route('/income-sources')
class ClientIncomeSources(Resource):
    @api.doc('Gets Income Sources')
    @api.marshal_list_with(_income_source, envelope='data')
    @portal_token_required
    def get(self):
        """ Gets Income Sources """
        income_sources = get_all_income_sources()

        return income_sources, 200

@api.route('/monthly-expenses')
class ClientMonthlyExpenses(Resource):
    @api.doc('Gets client Monthly Expenses')
    @api.marshal_list_with(_monthly_expense, envelope='data')
    @portal_token_required
    def get(self):
        """ Gets Monthly Expenses """
        monthly_expenses = get_all_monthly_expenses()

        return monthly_expenses, 200