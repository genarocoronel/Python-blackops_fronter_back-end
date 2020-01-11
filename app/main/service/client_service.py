import uuid
import datetime

from app.main import db
from app.main.model import Frequency
from app.main.model.appointment import Appointment
from app.main.model.client import Client, ClientType, ClientEmployment, ClientIncome, ClientMonthlyExpense, ClientContactNumber
from app.main.model.employment import Employment
from app.main.model.income import IncomeType, Income
from app.main.model.monthly_expense import MonthlyExpense, ExpenseType
from app.main.model.address import Address


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
        zip4=data.get('zip4'),
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


def create_client_from_candidate(candidate, client_type=ClientType.lead):
    new_client = Client(
        public_id=str(uuid.uuid4()),
        email=candidate.email,
        suffix=candidate.suffix,
        first_name=candidate.first_name,
        middle_initial=candidate.middle_initial,
        last_name=candidate.last_name,
        address=candidate.address,
        city=candidate.city,
        state=candidate.state,
        zip=candidate.zip,
        zip4=candidate.zip4,
        estimated_debt=candidate.estimated_debt,
        language=candidate.language,
        phone= candidate.phone,
        type=client_type,
        inserted_on=datetime.datetime.utcnow(),
    )
    for income in candidate.income_sources:
        new_client_income = ClientIncome(
            client=new_client,
            income_source=income.income_source
        )
        db.session.add(new_client_income)
    for expense in candidate.monthly_expenses:
        new_client_monthly_expense = ClientMonthlyExpense(
            client=new_client,
            monthly_expense=expense.monthly_expense
        )
        db.session.add(new_client_monthly_expense)
    for address in candidate.addresses:
        new_client.addresses.append(address)

    for number in candidate.contact_numbers:
        new_client_contact_number = ClientContactNumber(
            client=new_client,
            contact_number=number.contact_number
        )
        db.session.add(new_client_contact_number)

    new_client.credit_report_account = candidate.credit_report_account

    save_changes(new_client)
    return new_client

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


def update_client_addresses(client, addresses):
    prev_addresses = Address.query.filter_by(client_id=client.id).all()

    for address in addresses:
         new_address = Address(
            client_id=client.id,
            address1=address['address1'],
            address2=address['address2'],
            zip_code=address['zip_code'],
            city=address['city'],
            state=address['state'],
            from_date=datetime.datetime.strptime(address['fromDate'], "%Y-%m-%d"),
            to_date=datetime.datetime.strptime(address['toDate'], "%Y-%m-%d"),
            type=address['type']
         )
         db.session.add(new_address)
    for prev_address in prev_addresses:
        Address.query.filter_by(id=prev_address.id).delete()
    save_changes()
    return {'message': 'Successfully updated client addresses'}, None


def get_client_addresses(client):
    addresses = Address.query.filter_by(client_id=client.id).all()
    return addresses, None

def get_client_income_sources(client):
    income_sources_assoc = ClientIncome.query.join(Client).filter(Client.id == client.id).all()
    income_sources = [assoc.income_source for assoc in income_sources_assoc]
    income_types = IncomeType.query.filter(
        IncomeType.id.in_([income.income_type_id for income in income_sources])
    ).all()

    response = []
    for income in income_sources:
        data = {}
        data['income_type_id'] = income.income_type_id
        data['income_type'] = next(
            (income_type.name for income_type in income_types if income_type.id == income.income_type_id), 'UNKNOWN')
        data['value'] = income.value
        data['frequency'] = income.frequency
        response.append(data)
    return response, None


def update_client_income_sources(client, income_sources):
    prev_income_sources_assoc = ClientIncome.query.join(Client).filter(Client.id == client.id).all()

    # create new records first
    for data in income_sources:
        income_type = IncomeType.query.filter_by(id=data.get('income_type_id')).first()
        if income_type:
            new_candidate_income = ClientIncome()
            new_candidate_income.candidate = client
            new_candidate_income.income_source = Income(
                inserted_on=datetime.datetime.utcnow(),
                income_type_id=data.get('income_type_id'),
                value=data.get('value'),
                frequency=Frequency[data.get('frequency')]
            )
            db.session.add(new_candidate_income)
        else:
            return None, 'Invalid Income Type'

    # remove previous records
    for income_assoc in prev_income_sources_assoc:
        ClientIncome.query.filter(ClientIncome.candidate_id == client.id,
                                  ClientIncome.income_id == income_assoc.income_id).delete()
        Income.query.filter_by(id=income_assoc.income_id).delete()
    save_changes()

    return {'message': 'Successfully updated income sources'}, None


def get_client_monthly_expenses(client):
    monthly_expense_assoc = ClientMonthlyExpense.query.join(Client).filter(Client.id == client.id).all()
    monthly_expenses = [assoc.income_source for assoc in monthly_expense_assoc]
    expense_types = ExpenseType.query.filter(
        ExpenseType.id.in_([expense.expense_type_id for expense in monthly_expenses])
    ).all()

    response = []
    for expense in monthly_expenses:
        data = {}
        data['expense_type_id'] = expense.expense_type_id
        data['expense_type'] = next(
            (expense_type.name for expense_type in expense_types if expense_type.id == expense.expense_type_id), 'UNKNOWN')
        data['value'] = expense.value
        response.append(data)
    return response, None


def update_client_monthly_expenses(client, expenses):
    prev_monthly_expense_assoc = ClientMonthlyExpense.query.join(Client).filter(Client.id == client.id).all()

    # create new records first
    for data in expenses:
        expense_type = ExpenseType.query.filter_by(id=data.get('expense_type_id')).first()
        if expense_type:
            new_candidate_expense = ClientMonthlyExpense()
            new_candidate_expense.candidate = client
            new_candidate_expense.monthly_expense = MonthlyExpense(
                inserted_on=datetime.datetime.utcnow(),
                expense_type_id=data.get('expense_type_id'),
                value=data.get('value'),
            )
            db.session.add(new_candidate_expense)
        else:
            return None, 'Invalid Income Type'

    # remove previous records
    for expense_assoc in prev_monthly_expense_assoc:
        ClientMonthlyExpense.query.filter(ClientMonthlyExpense.candidate_id == client.id,
                                          ClientMonthlyExpense.expense_id == expense_assoc.expense_id).delete()
        MonthlyExpense.query.filter_by(id=expense_assoc.expense_id).delete()
    save_changes()

    return {'message': 'Successfully updated monthly expenses'}, None
