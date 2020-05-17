import os
import uuid
import time
import datetime

from flask import g, current_app as app

from app.main import db
from app.main.model.client import Client, ClientMonthlyExpense, ClientIncome
from app.main.model.income import IncomeType
from app.main.model.monthly_expense import ExpenseType

def get_all_monthly_expenses():
    """ Gets all monthly expenses """
    monthly_expense_assoc = ClientMonthlyExpense.query.join(Client).all()
    monthly_expenses = [assoc.monthly_expense for assoc in monthly_expense_assoc]
    expense_types = ExpenseType.query.filter(
        ExpenseType.id.in_([expense.expense_type_id for expense in monthly_expenses])
    ).all()

    response = []
    for expense in monthly_expenses:
        data = {}
        data['expense_type_id'] = expense.expense_type_id
        data['expense_type'] = next(
            (expense_type.name for expense_type in expense_types if expense_type.id == expense.expense_type_id), 'UNKNOWN')
        data['value'] = expense.value
        response.append(data)

    return response, None

def get_all_income_sources():
    """ Gets all income sources """
    income_sources_assoc = ClientIncome.query.join(Client).all()
    income_sources = [assoc.income_source for assoc in income_sources_assoc]
    income_types = IncomeType.query.filter(
        IncomeType.id.in_([income.income_type_id for income in income_sources])
    ).all()

    response = []
    for income in income_sources:
        data = {}
        data['income_type_id'] = income.income_type_id
        data['income_type'] = next(
            (income_type.name for income_type in income_types if income_type.id == income.income_type_id), 'UNKNOWN')
        data['value'] = income.value
        data['frequency'] = income.frequency
        response.append(data)
    return response, None