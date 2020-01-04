import datetime
from typing import List

from pytz import utc

from app.main import db
from app.main.model.monthly_expense import ExpenseType

expense_types = [
    {'name': 'rent_or_mortgage', 'display_name': 'Rent / Mortgage'},
    {'name': 'auto_payment', 'display_name': 'Auto Payment'},
    {'name': 'communication', 'display_name': 'Phone / Internet / Cable'},
    {'name': 'utilities', 'display_name': 'Utilities'},
    {'name': 'insurance', 'display_name': 'Insurance'},
    {'name': 'medical', 'display_name': 'Medical'},
    {'name': 'education', 'display_name': 'Education'},
    {'name': 'child_care', 'display_name': 'Child Care'},
    {'name': 'auto', 'display_name': 'Auto (Gas & Other)'},
    {'name': 'entertainment', 'display_name': 'Retail / Entertainment'},
    {'name': 'other', 'display_name': 'Other'},

]  # type: List[dict]


def seed_expense_type_values():
    for expense_type in expense_types:
        existing_expense_type = ExpenseType.query.filter_by(name=expense_type['name']).first()
        if not existing_expense_type:
            new_expense_type = ExpenseType(name=expense_type['name'], display_name=expense_type['display_name'],
                                           inserted_on=datetime.datetime.now(tz=utc))
            db.session.add(new_expense_type)
    db.session.commit()
