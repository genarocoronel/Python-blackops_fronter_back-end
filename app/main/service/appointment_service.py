import datetime
import uuid

from app.main import db
from app.main.model.appointment import Appointment


def save_new_appointment(data):
    date = datetime.datetime.strptime(data['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
    new_appointment = Appointment(
        client_id=data['client_id'],
        employee_id=data['employee_id'],
        datetime=date,
        summary=data['summary'],
        notes=data['notes'],
        reminder_types=data['reminder_types'],
        status='created',
        public_id=str(uuid.uuid4()),
    )
    save_changes(new_appointment)
    response_object = {
        'status': 'success',
        'message': 'Successfully created appointment'
    }
    return response_object, 201


def update_appointment(data):
    response_object = {
        'status': 'failed',
        'message': 'Unsupported method'
    }
    return response_object, 500


def get_all_appointments():
    return Appointment.query.all()


def get_appointment(public_id):
    return Appointment.query.filter_by(public_id=public_id).first()


def save_changes(data):
    db.session.add(data)
    db.session.commit()
