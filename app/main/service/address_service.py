import uuid
import datetime

from app.main import db
from app.main.model.address import Address


def save_new_address(address):
    save_changes(Address(
        public_id=str(uuid.uuid4()),
        candidate_id=address['candidate_id'],
        client_id=address['client_id'],
        address1=address['address1'],
        address2=address['address2'],
        zip_code=address['zip_code'],
        city=address['city'],
        state=address['state'],
        from_date=datetime.datetime.strptime(address['fromDate'], "%Y-%m-%d"),
        to_date=datetime.datetime.strptime(address['toDate'], "%Y-%m-%d"),
        type=address['type'],
    ))


def save_changes(data):
    db.session.add(data)
    db.session.commit()
