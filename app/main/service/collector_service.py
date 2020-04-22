import uuid
import datetime

from flask import current_app as app
from app.main.core.errors import BadRequestError, NotFoundError
from app.main import db
from app.main.model.collector import DebtCollector
from app.main.service.user_service import get_request_user


def get_all_collectors():
    """ Gets all Debt Collectors """
    collectors = []
    collector_records = DebtCollector.query.filter_by().all()

    if collector_records:
        for collector_item in collector_records:
            tmp_collector = synth_collector(collector_item)
            collectors.append(tmp_collector)

    return collectors


def create_collector(data):
    """ Creates a new Debt Collector """
    curr_user = get_request_user()
    existing_collector = DebtCollector.query.filter_by(name=data['name']).first()
    if not existing_collector:
        coll = DebtCollector(
            public_id = str(uuid.uuid4()),
            name=data['name'],
            phone=data['phone'],
            fax=data['fax'],
            address=data['address'],
            city=data['city'],
            state=data['state'],
            zip_code=data['zip_code'],
            inserted_on=datetime.datetime.utcnow(),
            created_by_username = curr_user.username,
            updated_on=datetime.datetime.utcnow(),
            updated_by_username=curr_user.username
        )

        db.session.add(coll)
        _save_changes()
    else:
        coll = existing_collector

    return synth_collector(coll)


def synth_collector(collector):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    collector_synth = {
        'public_id': collector.public_id,
        'name': collector.name,
        'phone': collector.phone,
        'fax': collector.fax,
        'address': collector.address,
        'city': collector.city,
        'state': collector.state,
        'zip_code': collector.zip_code
    }

    return collector_synth


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()