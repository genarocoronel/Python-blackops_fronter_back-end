import uuid
import datetime

from app.main import db
from app.main.model.client import Client


def save_new_client(data):
    client = Client.query.filter_by(email=data['email']).first()
    if not client:
        new_client = Client(
            public_id=str(uuid.uuid4()),
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            language=data['language'],
            phone=data['phone'],
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


def get_all_clients():
    return Client.query.all()


def get_client(public_id):
    return Client.query.filter_by(public_id=public_id).first()


def save_changes(data):
    db.session.add(data)
    db.session.commit()
