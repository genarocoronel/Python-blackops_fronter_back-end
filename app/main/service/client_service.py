import uuid
import datetime

from phonenumbers import PhoneNumber

from app.main.core.helper import generate_rand_code
from app.main import db
from app.main.model import Frequency
from app.main.model.appointment import Appointment
from app.main.model.client import Client, ClientType, ClientEmployment, ClientIncome, ClientCheckList, \
    ClientMonthlyExpense, ClientContactNumber, ClientDisposition, ClientDispositionType, EmploymentStatus, ClientCampaign
from app.main.model.user import UserClientAssignment
from app.main.model.user import UserLeadAssignment
from app.main.model.employment import Employment
from app.main.model.income import IncomeType, Income
from app.main.model.monthly_expense import MonthlyExpense, ExpenseType
from app.main.model.address import Address, AddressType
from app.main.model.credit_report_account import CreditReportAccount, CreditReportData
from app.main.model.contact_number import ContactNumber, ContactNumberType
from app.main.model.checklist import CheckList
from app.main.model.notification import NotificationPreference
from app.main.model.user import User
from app.main.channels import notification
from app.main.service.lead_distro import LeadDistroSvc
from sqlalchemy import desc, asc, or_, and_
from flask import current_app as app


def save_new_client(data, client_type=ClientType.lead):
    dispo = ClientDisposition.query.filter_by(name='Sales_ActiveStatus_InsertedLead').first()
    if not dispo:
        raise Exception('Error finding Client disposition record for "Inserted"')

    total_debt = data.get('estimated_debt')
    total_debt = 0 if total_debt is None else int(total_debt)

    new_client = Client(
        public_id=str(uuid.uuid4()),
        email=data.get('email'),
        first_name=data.get('first_name'),
        middle_initial=data.get('middle_initial'),
        last_name=data.get('last_name'),
        estimated_debt=total_debt,
        language=data.get('language'),
        ssn=data.get('ssn'),
        type=client_type,
        disposition_id=dispo.id,
        inserted_on=datetime.datetime.utcnow()
    )
    save_changes(new_client)
    assign_friendly_id(new_client)

    # current address
    # zip_code NOT NULL field
    address1 = '' if data.get('address') is None else data.get('address')
    zip_code = '' if data.get('zip_code') is None else data.get('zip_code')
    city = '' if data.get('city') is None else data.get('city')
    state = '' if data.get('state') is None else data.get('state')

    addr = Address(client_id=new_client.id,
                   address1=address1,
                   zip_code=zip_code,
                   city=city,
                   state=state,
                   type=AddressType.CURRENT)
    save_changes(addr)

    # contact number
    mobile_ph_number = '' if data.get('mobile_phone') is None else data.get('mobile_phone')
    number_type = ContactNumberType.query.filter_by(name='Cell Phone').first()
    cn = ContactNumber(inserted_on=datetime.datetime.utcnow(),
                       contact_number_type_id=number_type.id,
                       phone_number=mobile_ph_number)
    save_changes(cn)
    ccn = ClientContactNumber(client_id=new_client.id,
                              contact_number_id=cn.id)
    save_changes(ccn)

    # notification preference
    np = NotificationPreference(client_id=new_client.id)
    save_changes(np)

    # auto assignment
    svc = LeadDistroSvc()
    user = svc.assign_lead(new_client)
    if user:
        new_client.msg = 'You have been assigned a new Lead-Contact within 15 minutes.'
        notification.ClientNoticeChannel.send(user.id,
                                              new_client)

    return new_client, 201


def create_client_from_candidate(candidate, prequal_number, client_type=ClientType.lead):
    inserted_dispo = ClientDisposition.query.filter_by(name='Sales_ActiveStatus_InsertedLead').first()
    if not inserted_dispo:
        raise Exception('Error finding Client disposition record for "Inserted"')

    new_client = Client(
        public_id=str(uuid.uuid4()),
        friendly_id=prequal_number,
        email=candidate.email,
        suffix=candidate.suffix,
        first_name=candidate.first_name,
        middle_initial=candidate.middle_initial,
        last_name=candidate.last_name,
        estimated_debt=candidate.estimated_debt,
        employment_status=candidate.employment_status,
        language=candidate.language,
        dob=candidate.dob,
        type=client_type,
        disposition_id=inserted_dispo.id,
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
    # notification preference
    np = NotificationPreference(client_id=new_client.id)
    db.session.add(np)

    for employment_item in candidate.employments:
        new_client_employment = ClientEmployment(
            client=new_client,
            employment=employment_item.employment
        )
        db.session.add(new_client_employment)

    save_changes(new_client)

    # copy the campaign
    if candidate.campaign:
        ccamp = ClientCampaign(client_id=new_client.id,
                               campaign_id=candidate.campaign_id)
        db.session.add(ccamp)
        db.session.commit()

    # auto lead assignment
    # TODO Spanish clients
    svc = LeadDistroSvc()
    user = svc.assign_lead(new_client)
    if user:
        new_client.msg = 'You have been assigned a new Lead-Contact within 15 minutes.'
        notification.ClientNoticeChannel.send(user.id,
                                              new_client)

    return new_client


def assign_friendly_id(client):
    """ Assigns a random Friendly ID to the given Client """
    friendly_id = generate_rand_code(8, client.public_id)
    max_tries = 3;
    current_tries = 1;

    while does_friendly_id_exists(friendly_id):
        friendly_id = generate_rand_code(8, client.public_id)
        current_tries +1
        if current_tries > max_tries:
            raise Exception(f'Tried x3 times to generate a friendly ID without success for Client with ID {client.id}')
    
    client.friendly_id = friendly_id
    save_changes(client)

    return client


def get_all_clients(client_type=ClientType.client):
    # TODO - Refactor to use user_service::get_lead_assignments(), and user_service::get_client_assignments()
    # when frontend assigment feature ready
    return Client.query.filter_by(type=client_type).all()


def client_filter(limit=25, sort_col='id', order="desc",
                  pageno=1, search_fields=None, search_val="",
                  dt_fields=None, from_date=None, to_date=None,
                  numeric_fields=None, client_type=ClientType.client):
    try:
        # sorting
        total = 0
        type_str = 'clients' if client_type == ClientType.client else 'leads'

        sort = desc(sort_col) if order == 'desc' else asc(sort_col)
        # base query
        query = Client.query.filter(Client.type!=ClientType.coclient).outerjoin(ClientDisposition) \
            .outerjoin(CreditReportAccount) \
            .outerjoin(Address) \
            # .outerjoin(ClientContactNumber)
        # print("this is query", query)
        # search fields
        if search_fields is not None:
            _or_filts = []
            _and_filts = []
            # iterate through search fields 
            for field in search_fields:
                filt = None
                tokens = field.split(':')
                and_exp = False
                if len(tokens) > 1:
                    and_exp = True
                    field = tokens[0].strip()
                    search = "%{}%".format(tokens[1].strip())
                    e_val = tokens[1].strip()
                else:
                    if search_val is not None or search_val.strip() != '':
                        search = "%{}%".format(search_val)
                        e_val = search_val
                    else:
                        continue

                # enum fields in string
                if 'employment_status' in field:
                    rep = EmploymentStatus.frm_text(e_val)
                    if rep is not None:
                        filt = (Client.employment_status == rep)
                # relationship fields
                else:
                    if 'disposition' in field:
                        column = getattr(ClientDisposition, 'value', None)
                    else:
                        column = getattr(Client, field, None)
                    filt = column.ilike(search)

                # append to the filters
                if filt is not None:
                    if and_exp is True:
                        _and_filts.append(filt)
                    else:
                        _or_filts.append(filt)
            # check if filters are present
            if len(_or_filts) == 0 and len(_and_filts) == 0:
                return {type_str: [], "page_number": pageno, "total_records": total, "limit": limit}
            else:
                if len(_or_filts) > 0:
                    query = query.filter(or_(*_or_filts))
                if len(_and_filts) > 0:
                    query = query.filter(and_(*_and_filts))

        # datetime fields
        if dt_fields is not None:
            for field in dt_fields:
                column = getattr(Client, field, None)
                if from_date is not None and to_date is not None:
                    query = query.filter(and_(column >= from_date, column <= to_date))
                elif from_date is not None:
                    query = query.filter(column >= from_date)
                elif to_date is not None:
                    query = query.filter(column <= to_date)
                else:
                    raise ValueError("Not a valid datetime filter query")

        # Numeric fields
        if numeric_fields is not None:
            for field in numeric_fields:
                tokens = field.split(':')
                if len(tokens) < 3:
                    continue
                # format  field:op:val
                field = tokens[0].strip()
                op = tokens[1].strip()
                val = float(tokens[2].strip())
                column = getattr(Client, field, None)

                if column is None:
                    raise ValueError("Not a valid numeric column")

                if op == 'lt':
                    query = query.filter(column < val)
                elif op == 'lte':
                    query = query.filter(column <= val)
                elif op == 'gt':
                    query = query.filter(column > val)
                elif op == 'gte':
                    query = query.filter(column >= val)
                elif op == 'eq':
                    query = query.filter(column == val)
                else:
                    raise ValueError("Not a valid numeric operation")

        total = query.count()
        query = query.order_by(sort).paginate(pageno, limit, False)
        records = query.items

        return {'data': records, "page_number": pageno, "total_records": total, "limit": limit}


    except Exception as err:
        app.logger.warning('Client filter issue, {}'.format(str(err)))
        raise ValueError("Invalid Client filter query")


def get_client(public_id, client_type=ClientType.client):
    client = Client.query.filter_by(public_id=public_id)\
                         .join(CreditReportAccount)\
                         .outerjoin(ClientDisposition)\
                         .outerjoin(Address).first()
    if client:
        app.logger.info(f"Found a Client with ID {public_id} and has Credit Report Account")
        return client 
    else:
        client = Client.query.filter_by(public_id=public_id).first()
        if client:
            app.logger.info(f"Found a Client with ID {public_id} and does NOT have a Credit Report Account")
    return client


def get_client_by_public_id(id):
    """ Gets a client by public ID """
    return Client.query.filter_by(public_id=id).first()


def does_friendly_id_exists(friendly_id):
    """ Gets wheter a friendly ID exists """
    does_exist = False
    if Client.query.filter_by(friendly_id=friendly_id).first():
        does_exist = True
    return does_exist


def get_client_by_id(id):
    """ Gets a client by (internal) ID """
    return Client.query.filter_by(id=id).first()


def get_client_contact_by_phone(phone_no: PhoneNumber):
    assert phone_no is not None

    client_cn = ClientContactNumber.query \
        .join(ContactNumber) \
        .filter(ContactNumber.phone_number == str(phone_no.national_number)).first()
    return client_cn


def get_client_by_phone(phone_number):
    """ Gets a Client record by phone number """
    client = None
    contactnum_assoc = ClientContactNumber.query.join(ContactNumber).filter(ContactNumber.phone_number == phone_number).first()
    if contactnum_assoc:
        client = contactnum_assoc.client
    return client


def update_client(client, data, client_type=ClientType.client):
    if client:
        for attr in data:
            if hasattr(client, attr):
                if attr == 'disposition':
                    disposition = ClientDisposition.query.filter_by(value=data.get(attr)).first()
                    if disposition:
                        if disposition.select_type == ClientDispositionType.MANUAL:
                            setattr(client, 'disposition_id', disposition.id)
                    else:
                        response_object = {
                            'success': False,
                            'message': 'Invalid Disposition to update manually',
                        }
                        return response_object, 400
                elif attr == 'sales_rep_id':
                    # notify the user
                    user_id = data.get(attr)
                    assign_salesrep(client, user_id)
                elif attr == 'account_manager_id':
                    # notify the user
                    user_id = data.get(attr)
                    assign_servicerep(client, user_id)
                else:
                    setattr(client, attr, data.get(attr))

        save_changes(client)
        client.update()

        return client
    else:
        response_object = {
            'success': False,
            'message': f'{client_type.name.capitalize()} not found',
        }
        return response_object, 404


def assign_salesrep(client, user_public_id):
    """ Assigns a Sales Rep user to a Lead """
    # fetch the user
    user = User.query.filter_by(public_id=user_public_id).first()
    if not user:
        raise ValueError('Sales Rep not found')

    assignment = UserLeadAssignment.query.filter_by(client_id=client.id).first()
    if assignment:
        assignment.user_id = user.id
    else:
        assignment = UserLeadAssignment(
            user_id = user.id,
            client_id = client.id
        )
    # set in client 
    client.sales_rep_id = user.id

    db.session.add(assignment)
    save_changes()

    # update the sales metrics
    distro = LeadDistroSvc()
    distro.on_manual_assign(client, user)
    
    client.msg = 'You have been assigned a new Lead-Contact within 15 minutes.'
    notification.ClientNoticeChannel.send(user.id,
                                          client)
    return True

def assign_servicerep(client, user_public_id):
    """ Assigns a Service Rep user to a Client """
    user = User.query.filter_by(public_id=user_public_id).first()
    if not user:
        raise ValueError('Service Rep not found')

    assignment = UserClientAssignment.query.filter_by(client_id=client.id).first()
    if assignment:
        assignment.user_id = user.id
    else:
        assignment = UserClientAssignment(
            user_id = user.id,
            client_id = client.id
        )

    db.session.add(assignment)
    # tmp: support for legacy features
    client.account_manager_id = user.id 

    save_changes()
    client.msg = 'New Client assigned, please follow up.'
    notification.ClientNoticeChannel.send(user.id,
                                          client)            
    
    return True

def get_client_bank_account(client):
    if isinstance(client, str):
        client = get_client(client)
    if not isinstance(client, Client):
        raise ValueError('accepts client public_id or client object')

    return client.bank_account


def get_client_appointments(public_id, client_type=ClientType.client):
    client = get_client(public_id)
    if client:
        return Appointment.query.filter_by(client_id=client.id).all()
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
        data['employer_name'] = employment.employer_name
        data['start_date'] = employment.start_date
        data['end_date'] = employment.end_date
        data['gross_salary'] = employment.gross_salary
        data['gross_salary_frequency'] = employment.gross_salary_frequency
        data['other_income'] = employment.other_income
        data['other_income_frequency'] = employment.other_income_frequency
        data['current'] = employment.current
        employment_data.append(data)

    return employment_data, None


def get_all_clients_dispositions():
    return ClientDisposition.query.filter_by().all()


def update_client_employments(client, employments):
    # create new records first
    for data in employments:
        start_date = datetime.datetime.utcnow() if data.get('start_date') is None else data.get('start_date')
        employer_name = "" if data.get('employer_name') is None else data.get('employer_name')
        gross_salary = 0 if data.get('gross_salary') is None else data.get('gross_salary')

        client_emplyoment = ClientEmployment.query.join(Client) \
            .join(Employment) \
            .filter(and_(Client.id == client.id, Employment.current == data.get('current'))).first()
        if client_emplyoment is None:
            client_employment = ClientEmployment()
            client_employment.employment = Employment(
                inserted_on=datetime.datetime.utcnow(),
                employer_name=employer_name,
                start_date=start_date,
                end_date=data.get('end_date'),
                gross_salary=gross_salary,
                gross_salary_frequency=data.get('gross_salary_frequency'),
                other_income=data.get('other_income'),
                other_income_frequency=data.get('other_income_frequency'),
                current=data.get('current')
            )
            client_employment.client = client
            save_changes(client_employment)
        else:
            empl = client_emplyoment.employment
            empl.employer_name = employer_name
            empl.start_date = start_date
            empl.end_date = data.get('end_date')
            empl.gross_salary = gross_salary
            empl.gross_salary_frequency = data.get('gross_salary_frequency')
            empl.other_income = data.get('other_income')
            empl.other_income_frequency = data.get('other_income_frequency')
            save_changes()
    # update status 
    client.update()

    return {'message': 'Successfully updated employments'}, None


def update_client_addresses(client, addresses):
    for address in addresses:
        addr1 = '' if address['address1'] is None else address['address1']
        addr2 = address['address2'] if 'address2' in address else None
        zip_code = '' if address['zip_code'] is None else address['zip_code']
        city = '' if address['city'] is None else address['city']
        state = '' if address['state'] is None else address['state']

        from_date = datetime.datetime.utcnow()
        to_date = datetime.datetime.utcnow()
        if address['from_date'] != '':
            from_date = datetime.datetime.strptime(address['from_date'], "%Y-%m-%d")
        if address['to_date'] != '':
            to_date = datetime.datetime.strptime(address['to_date'], "%Y-%m-%d")
        # check already exists,if exists update
        # else create new one
        client_address = Address.query.filter_by(client_id=client.id,
                                                 type=address['type']).first()
        if client_address is None:
            client_address = Address(client_id=client.id,
                                     address1=addr1,
                                     address2=addr2,
                                     zip_code=zip_code,
                                     city=city,
                                     state=state,
                                     from_date=from_date,
                                     to_date=to_date,
                                     type=address['type'])
            save_changes(client_address)
        else:
            client_address.address1 = addr1
            client_address.address2 = addr2
            client_address.zip_code = zip_code
            client_address.city = city
            client_address.state = state
            client_address.from_date = from_date
            client_address.to_date = to_date
            save_changes()

    client.update()

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
    for data in income_sources:
        income_type_id = data.get('income_type_id')
        income_val = data.get('value')

        client_income = ClientIncome.query.join(Client) \
            .join(Income) \
            .filter(and_(Client.id == client.id, Income.income_type_id == income_type_id)).first()
        if client_income is None:
            income = Income(inserted_on=datetime.datetime.utcnow(),
                            income_type_id=income_type_id,
                            value=income_val,
                            frequency=Frequency[data.get('frequency')])
            save_changes(income)
            client_income = ClientIncome(client_id=client.id, income_id=income.id)
            save_changes(client_income)
        else:
            client_income.income_source.value = income_val
            client_income.income_source.frequency = Frequency[data.get('frequency')]
            db.session.commit()

    client.update()

    return {'message': 'Successfully updated income sources'}, None


def get_client_monthly_expenses(client):
    monthly_expense_assoc = ClientMonthlyExpense.query.join(Client).filter(Client.id == client.id).all()
    monthly_expenses = [assoc.monthly_expense for assoc in monthly_expense_assoc]
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
    for data in expenses:
        expense_type_id = data.get('expense_type_id')
        expense_val = data.get('value')

        cme = ClientMonthlyExpense.query.join(Client) \
            .join(MonthlyExpense) \
            .filter(and_(Client.id == client.id, MonthlyExpense.expense_type_id == expense_type_id)).first()
        if cme is None:
            monthly_expense = MonthlyExpense(inserted_on=datetime.datetime.utcnow(),
                                             expense_type_id=expense_type_id,
                                             value=expense_val)
            save_changes(monthly_expense)
            cme = ClientMonthlyExpense(client_id=client.id, expense_id=monthly_expense.id)
            save_changes(cme)
        else:
            cme.monthly_expense.value = expense_val
            db.session.commit()
    # update status
    client.update()

    return {'message': 'Successfully updated monthly expenses'}, None


def get_client_contact_numbers(client):
    contact_number_assoc = ClientContactNumber.query.join(Client).filter(Client.id == client.id).all()
    contact_numbers = [num.contact_number for num in contact_number_assoc]
    phone_types = ContactNumberType.query.filter(
        ContactNumberType.id.in_([num.contact_number_type_id for num in contact_numbers])).all()

    number_data = []
    for contact_number in contact_numbers:
        data = {}
        data['phone_type_id'] = contact_number.contact_number_type_id
        data['phone_type'] = next(
            (phone_type.name for phone_type in phone_types if phone_type.id == contact_number.contact_number_type_id),
            'UNKNOWN')
        data['phone_number'] = contact_number.phone_number
        data['preferred'] = contact_number.preferred
        number_data.append(data)

    return number_data, None


def update_client_contact_numbers(client, contact_numbers):
    ## contact number list
    for data in contact_numbers:
        phone_type_id = data.get('phone_type_id')
        phone_type = data.get('phone_type')
        phone_number = data.get('phone_number')
        preferred = data.get('preferred')

        # check already exists,if exists update
        # else create new one
        ccn = ClientContactNumber.query.join(Client) \
            .join(ContactNumber) \
            .filter(and_(Client.id == client.id, ContactNumber.contact_number_type_id == phone_type_id)).first()
        if ccn is None:
            new_cn = ContactNumber(inserted_on=datetime.datetime.utcnow(),
                                   contact_number_type_id=phone_type_id,
                                   phone_number=phone_number,
                                   preferred=preferred)
            save_changes(new_cn)
            new_ccn = ClientContactNumber(client_id=client.id, contact_number_id=new_cn.id)
            save_changes(new_ccn)
        else:
            cn = ccn.contact_number
            cn.phone_number = phone_number
            cn.preferred = preferred
            db.session.commit()

    client.update()

    return {'message': 'Successfully updated contact numbers'}, None


def get_co_client(client):
    # fetch the co-client
    co_client = client.co_client
    if co_client is not None:
        return co_client
    else:
        return {
        }


def update_co_client(client, data):
    co_client = client.co_client
    if co_client is None:
        # required fields
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        # optional fields
        mi = data.get('middle_initial').strip()
        dob = data.get('dob')
        ssn = data.get('ssn')
        language = data.get('language')

        # insert
        co_client = Client(public_id=str(uuid.uuid4()),
                           first_name=first_name,
                           last_name=last_name,
                           email=email,
                           middle_initial=mi,
                           dob=dob,
                           ssn=ssn,
                           language=language,
                           estimated_debt=0,
                           type=ClientType.coclient,
                           inserted_on=datetime.datetime.utcnow())
        save_changes(co_client)
        assign_friendly_id(co_client)
        client.co_client = co_client
        db.session.commit()

    else:
        # update
        for attr in data:
            if hasattr(co_client, attr):
                setattr(co_client, attr, data.get(attr))

        db.session.commit()

    client.update()

    return co_client


def get_client_checklist(client):
    result = []
    items = CheckList.query.all()
    if len(items) == 0:
        raise ValueError("No records in checklist table")
    try:
        client_items = [ccl.checklist_id for ccl in ClientCheckList.query.filter_by(client_id=client.id).all()]
        for item in items:
            cl = {
                'id': item.id,
                'title': item.title,
                'checked': True if item.id in client_items else False,
            }
            result.append(cl)
    except Exception:
        raise ValueError("Error in fetching client checklist")

    return result


def update_client_checklist(client, data):
    item = data
    # check the valid checklist item is valid or not
    cl = CheckList.query.filter_by(id=item['id']).first()
    if cl is None:
        raise ValueError("Checklist item is not valid")

    if item['checked']:
        ccl = ClientCheckList(client_id=client.id,
                              checklist_id=item['id'])
        save_changes(ccl)
    else:
        try:
            ClientCheckList.query.filter_by(client_id=client.id, checklist_id=item['id']).delete()
            db.session.commit()
        except Exception:
            raise ValueError("Not a valid checklist item for the client")

    client.update()


def update_notification_pref(client, data):
    try:
        pref = client.notification_pref
        if pref is None:
            pref = NotificationPreference(client_id=client.id)
            save_changes(pref)

        pref.service_call = data.get('service_call')
        pref.appt_reminder = data.get('appt_reminder')
        pref.doc_notification = data.get('doc_notification')
        pref.payment_reminder = data.get('payment_reminder')
        db.session.commit()

        client.update()
    except Exception as err:
        raise ValueError("Update preferences error: Invalid parameter")
                                   
# fetch client & coclient debts
def fetch_client_combined_debts(client):
    try:
        keys = [client.id,]
        if client.co_client:
            keys.append(client.co_client.id)

        debts = CreditReportData.query.outerjoin(CreditReportAccount)\
                                      .filter(CreditReportAccount.client_id.in_(keys)).all()
        return debts

    except Exception as err:
        raise ValueError("Fetch Combined debts error")

