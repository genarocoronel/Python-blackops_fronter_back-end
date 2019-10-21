import uuid
import datetime

from app.main import db
from app.main.model.appointment import Appointment
from app.main.model.client import Client, ClientType


def save_new_client(data, client_type=ClientType.lead):
    client = Client.query.filter_by(email=data['email']).first()
    if not client:
        new_client = Client(
            public_id=str(uuid.uuid4()),
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            language=data['language'],
            phone=data['phone'],
            type=client_type,
            inserted_on=datetime.datetime.utcnow()
        )
        save_changes(new_client)
        response_object = {
            'status': 'success',
            'message': 'Successfully created client'
        }
        return response_object, 201
    else:
        response_object = {
            'status': 'fail',
            'message': 'Client already exists'
        }
        return response_object, 409


def get_all_clients(client_type=ClientType.client):
    return Client.query.filter_by(type=client_type).all()


def get_client(public_id, client_type=ClientType.client):
    return Client.query.filter_by(public_id=public_id, type=client_type).first()


def get_client_appointments(public_id, client_type=ClientType.client):
    client = get_client(public_id)
    if client:
        return Appointment.query.filter_by(client_id=client.id, type=client_type).all()
    else:
        return None


def save_changes(data):
    db.session.add(data)
    db.session.commit()
