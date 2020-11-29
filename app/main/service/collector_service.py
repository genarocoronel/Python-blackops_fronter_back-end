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

def update_collector(collector_id, data):
    fields = {}
    curr_user = get_request_user()
    collector = DebtCollector.query.filter_by(public_id=collector_id).first()
    if not collector:
        raise ValueError("Debt Collector record not found")

    if data.get('name'):
        collector.name = data.get('name')
    if data.get('phone'):
        collector.phone = data.get('phone')
    if data.get('fax'):
        collector.fax = data.get('fax')
    if data.get('address'):
        collector.address = data.get('address')
    if data.get('city'):
        collector.city = data.get('city')
    if data.get('state'):
        collector.state = data.get('state')
    if data.get('zip_code'):
        collector.zip_code = data.get('zip_code')

    fields['updated_on'] = datetime.datetime.utcnow()   
    fields['updated_by_username'] = curr_user.username
    db.session.commit()

    return collector

def search_collector(request):
    result = []
    q = request.args.get('q', None)
    search_val = "%{}%".format(q)

    if q is not None:
        result = DebtCollector.query.filter(DebtCollector.name.ilike(search_val)).all()

    return result

def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()
