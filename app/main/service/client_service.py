import uuid
import datetime

from app.main import db
from app.main.model.appointment import Appointment
from app.main.model.client import Client, ClientType


def save_new_client(data, client_type=ClientType.lead):
    new_client = Client(
        public_id=str(uuid.uuid4()),
        email=data.get('email'),
        suffix=data.get('suffix'),
        first_name=data.get('first_name'),
        middle_initial=data.get('middle_initial'),
        last_name=data.get('last_name'),
        address=data.get('address'),
        city=data.get('city'),
        state=data.get('state'),
        zip=data.get('zip'),
        zip4=data.get('zip'),
        estimated_debt=data.get('estimated_debt'),
        language=data.get('language'),
        phone=data.get('phone'),
        type=client_type,
        inserted_on=datetime.datetime.utcnow()
    )

    save_changes(new_client)
    response_object = {
        'status': 'success',
        'message': 'Successfully created client'
    }
    return response_object, 201


def get_all_clients(client_type=ClientType.client):
    return Client.query.filter_by(type=client_type).all()


def get_client(public_id, client_type=ClientType.client):
    return Client.query.filter_by(public_id=public_id, type=client_type).first()


def update_client(client, data):
    pass


def get_client_bank_account(client):
    if isinstance(client, str):
        client = get_client(client)
    if not isinstance(client, Client):
        raise ValueError('accepts client public_id or client object')

    return client.bank_account


def get_client_appointments(public_id, client_type=ClientType.client):
    client = get_client(public_id)
    if client:
        return Appointment.query.filter_by(client_id=client.id, type=client_type).all()
    else:
        return None


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()