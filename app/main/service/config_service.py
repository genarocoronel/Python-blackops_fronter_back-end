from app.main import db
from app.main.model.contact_number import ContactNumberType
from app.main.model.income import IncomeType, Income
from app.main.model.candidate import CandidateDisposition
from app.main.model.client import ClientDisposition
from app.main.model.monthly_expense import ExpenseType, MonthlyExpense

def get_contact_number_types():
    return ContactNumberType.query.all()

def get_income_types():
    return IncomeType.query.all()

def get_expense_types():
    return ExpenseType.query.all()

def get_dispositions():
    return CandidateDisposition.query.all()

def get_all_candidates_dispositions():
    return CandidateDisposition.query.filter_by().all()

def get_all_clients_dispositions():
    return ClientDisposition.query.filter_by().all()