import uuid
import datetime

from app.main import db
from app.main.model.appointment import Appointment
from app.main.model.client import Client, ClientType, ClientEmployment
from app.main.model.employment import Employment


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


def get_client_employments(client):
    employment_assoc = ClientEmployment.query.join(Client).filter(Client.id == client.id).all()
    employments = [num.employment for num in employment_assoc]

    employment_data = []
    for employment in employments:
        data = {}
        data['start_date'] = employment.start_date
        data['end_date'] = employment.end_date
        data['gross_salary'] = employment.gross_salary
        data['gross_salary_frequency'] = employment.gross_salary_frequency
        data['other_income'] = employment.other_income
        data['other_income_frequency'] = employment.other_income_frequency
        data['current'] = employment.current
        employment_data.append(data)

    return employment_data, None


def update_client_employments(client, employments):
    prev_employments = ClientEmployment.query.join(Client).filter(Client.id == client.id).all()

    # create new records first
    for data in employments:
        new_employment = ClientEmployment()
        new_employment.client = client
        new_employment.employment = Employment(
            inserted_on=datetime.datetime.utcnow(),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            gross_salary=data.get('gross_salary'),
            gross_salary_frequency=data.get('gross_salary_frequency'),
            other_income=data.get('other_income'),
            other_income_frequency=data.get('other_income_frequency'),
            current=data.get('current')
        )
        db.session.add(new_employment)
    save_changes()

    # remove previous records
    for prev_employment in prev_employments:
        ClientEmployment.query.filter(ClientEmployment.client_id == client.id,
                                            ClientEmployment.employment_id == prev_employment.employment_id).delete()
        Employment.query.filter_by(id=prev_employment.employment_id).delete()
    save_changes()

    return {'message': 'Successfully updated employments'}, None

