import datetime

from pytz import utc

from app.main import db
from app.main.model.contact_number import ContactNumberType

contact_number_types = [
    {'name': 'Cell Phone', 'description': 'Mobile phone number'},
    {'name': 'Work Phone', 'description': 'Work phone number'},
    {'name': 'Home', 'description': 'Home phone number'}
]


def seed_contact_number_types():
    for types in contact_number_types:
        existing_contact_no_type = ContactNumberType.query.filter_by(name=types['name']).first()
        if not existing_contact_no_type:
            new_contact_no_type = ContactNumberType(name=types['name'], description=types['description'],
                                                    inserted_on=datetime.datetime.now(tz=utc))
            db.session.add(new_contact_no_type)
    db.session.commit()
