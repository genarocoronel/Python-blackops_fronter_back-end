import datetime

from pytz import utc

contact_number_types = [
    {'name': 'Cell Phone', 'description': 'Mobile phone number'},
    {'name': 'Work Phone', 'description': 'Work phone number'},
    {'name': 'Home', 'description': 'Home phone number'}
]


def seed_contact_number_types():
    db_values = []
    for types in contact_number_types:
        db_values.append(
            {'name': types['name'], 'description': types['description'], 'inserted_on': datetime.datetime.now(tz=utc)})
    return db_values
