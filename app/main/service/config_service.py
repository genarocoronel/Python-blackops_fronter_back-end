from app.main import db
from app.main.model.contact_number import ContactNumberType
from app.main.model.income import IncomeType, Income
from app.main.model.monthly_expense import ExpenseType, MonthlyExpense

def get_contact_number_types():
    return ContactNumberType.query.all()

def get_income_types():
    return IncomeType.query.all()

def get_expense_types():
    return ExpenseType.query.all()