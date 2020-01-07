import datetime
from typing import List

from pytz import utc

from app.main import db
from app.main.model.income import IncomeType

income_types = [
    {'name': 'household_income', 'display_name': 'Household Income'},
    {'name': 'alimony', 'display_name': 'Alimony'},
    {'name': 'child_support', 'display_name': 'Child Support'},
    {'name': 'other', 'display_name': 'Other'},
]  # type: List[dict]


def seed_income_types():
    for income_type in income_types:
        existing_income_type = IncomeType.query.filter_by(name=income_type['name']).first()
        if not existing_income_type:
            new_income_type = IncomeType(name=income_type['name'], display_name=income_type['display_name'],
                                         inserted_on=datetime.datetime.now(tz=utc))
            db.session.add(new_income_type)
    db.session.commit()
