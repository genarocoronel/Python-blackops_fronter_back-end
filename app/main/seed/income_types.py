import datetime
from typing import List

from pytz import utc

income_types = [
    {'name': 'household_income', 'display_name': 'Household Income'},
    {'name': 'alimony', 'display_name': 'Alimony'},
    {'name': 'child_support', 'display_name': 'Child Support'},
    {'name': 'other', 'display_name': 'Other'},
]  # type: List[dict]


def seed_income_types():
    db_values = []
    for income_type in income_types:
        db_values.append(
            {
                'name': income_type['name'],
                'display_name': income_type['display_name'],
                'inserted_on': datetime.datetime.now(tz=utc)
            })
    return db_values
