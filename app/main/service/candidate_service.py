import uuid
import datetime

from sqlalchemy import desc, asc, or_, and_
from app.main import db
from app.main.model.employment import Employment
from app.main.model import Frequency
from app.main.model.candidate import CandidateContactNumber, CandidateIncome, CandidateEmployment, \
    CandidateMonthlyExpense
from app.main.model.candidate import CandidateDisposition, CandidateDispositionType
from app.main.model.campaign import Campaign
from app.main.model.contact_number import ContactNumber, ContactNumberType
from app.main.model.candidate import CandidateImport, Candidate, CandidateStatus
from app.main.model.credit_report_account import CreditReportAccount
from app.main.model.income import IncomeType, Income
from app.main.model.monthly_expense import ExpenseType, MonthlyExpense
from app.main.model.address import Address, AddressType
from app.main.model.client import ClientType
from app.main.service.client_service import create_client_from_candidate

from flask import current_app as app


def save_new_candidate(data):
    
    exist_candidate = Candidate.query.filter(and_(Candidate.first_name == data.get('first_name'),
                                                  Candidate.last_name == data.get('last_name'),
                                                  Candidate.email == data.get('email'),
                                                  )).first()

    if exist_candidate is not None:
        response_object = {
            'success': False,
            'message': 'This candidate already exists'
        }
        return response_object, 409

    new_candidate = Candidate(
        public_id=str(uuid.uuid4()),
        email=data.get('email'),
        suffix=data.get('suffix'),
        first_name=data.get('first_name'),
        middle_initial=data.get('middle_initial'),
        last_name=data.get('last_name'),
        estimated_debt=data.get('estimated_debt'),
        language=data.get('language'),

        debt3=data.get('debt3'),
        debt15=data.get('debt15'),
        debt2=data.get('debt2'),
        debt215=data.get('debt215'),
        debt3_2=data.get('debt3_2'),
        checkamt=data.get('checkamt'),
        spellamt=data.get('spellamt'),
        debt315=data.get('debt315'),
        year_interest=data.get('year_interest'),
        total_interest=data.get('total_interest'),
        sav215=data.get('sav215'),
        sav15=data.get('sav15'),
        sav315=data.get('sav315'),

        inserted_on=datetime.datetime.utcnow(),
        import_record=data.get('import_record')
    )

    db.session.add(new_candidate)
    db.session.flush()
    db.session.refresh(new_candidate)

    new_address = Address(
        candidate_id=new_candidate.id,
        address1=data.get('address'),
        city=data.get('city'),
        zip_code=data.get('zip'),
        state=data.get('state'),
        type=AddressType.CURRENT
    )
    db.session.add(new_address)
    save_changes()

    response_object = {
        'success': True,
        'status': 'success',
        'message': 'Successfully created candidate'
    }
    return response_object, 201


def update_candidate(public_id, data):
    candidate = Candidate.query.filter_by(public_id=public_id).first()
    if candidate:
        for attr in data:
            if hasattr(candidate, attr):
                if attr == 'disposition':
                    desired_disposition = CandidateDisposition.query.filter_by(value=data.get(attr)).first()
                    # Do not update if disposition is unchanged, especially for internally managed dipositions
                    if desired_disposition.id != candidate.disposition_id:
                        if desired_disposition.select_type == CandidateDispositionType.MANUAL:
                            setattr(candidate, 'disposition_id', desired_disposition.id)
                        else:
                            response_object = {
                                'success': False,
                                'message': 'Invalid Disposition to update manually',
                            }
                            return response_object, 400
                
                elif attr == 'email':
                    # Do not udpate candidates.email with empty string, since it violates unique constraint
                    if data.get(attr) and data.get(attr) != '':
                        setattr(candidate, attr, data.get(attr))
                else:
                    setattr(candidate, attr, data.get(attr))

        save_changes(candidate)

        response_object = {
            'success': True,
            'message': 'Candidate updated successfully',
        }
        return response_object, 200
    else:
        response_object = {
            'success': False,
            'message': 'Candidate not found',
        }
        return response_object, 404


def get_candidate_employments(candidate):
    employment_assoc = CandidateEmployment.query.join(Candidate).filter(Candidate.id == candidate.id).all()
    employments = [candidate_employment.employment for candidate_employment in employment_assoc]
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


def update_candidate_employments(candidate, employments):
    # create new records first
    for data in employments:
        start_date = datetime.datetime.utcnow() if data.get('start_date') is None else data.get('start_date')
        employer_name = "" if data.get('employer_name') is None else data.get('employer_name')
        gross_salary = 0 if data.get('gross_salary') is None else data.get('gross_salary')

        candid_emplyoment = CandidateEmployment.query.join(Candidate)\
                                                     .join(Employment)\
                                                     .filter(and_(Candidate.id==candidate.id, Employment.current==data.get('current'))).first()
        if candid_emplyoment is None:
            candid_employment = CandidateEmployment()
            candid_employment.employment = Employment(
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
            candid_employment.candidate = candidate
            save_changes(candid_employment)
        else:
            empl = candid_emplyoment.employment
            empl.employer_name = employer_name
            empl.start_date = start_date
            empl.end_date = data.get('end_date')
            empl.gross_salary = gross_salary
            empl.gross_salary_frequency = data.get('gross_salary_frequency')
            empl.other_income = data.get('other_income')
            empl.other_income_frequency = data.get('other_income_frequency')
            save_changes()

    return {'message': 'Successfully updated employments'}, None


def get_candidate_income_sources(candidate):
    income_sources_assoc = CandidateIncome.query.join(Candidate).filter(Candidate.id == candidate.id).all()
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


def update_candidate_income_sources(candidate, income_sources):
    prev_income_sources_assoc = CandidateIncome.query.join(Candidate).filter(Candidate.id == candidate.id).all()

    # create new records first
    for data in income_sources:
        income_type = IncomeType.query.filter_by(id=data.get('income_type_id')).first()
        if income_type:
            new_candidate_income = CandidateIncome()
            new_candidate_income.candidate = candidate
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
        CandidateIncome.query.filter(CandidateIncome.candidate_id == candidate.id,
                                     CandidateIncome.income_id == income_assoc.income_id).delete()
        Income.query.filter_by(id=income_assoc.income_id).delete()
    save_changes()

    return {'message': 'Successfully updated income sources'}, None


def get_candidate_monthly_expenses(candidate):
    monthly_expense_assoc = CandidateMonthlyExpense.query.join(Candidate).filter(Candidate.id == candidate.id).all()
    monthly_expenses = [assoc.monthly_expense for assoc in monthly_expense_assoc]
    expense_types = ExpenseType.query.filter(
        ExpenseType.id.in_([expense.expense_type_id for expense in monthly_expenses])
    ).all()

    response = []
    for expense in monthly_expenses:
        data = {}
        data['expense_type_id'] = expense.expense_type_id
        data['expense_type'] = next(
            (expense_type.name for expense_type in expense_types if expense_type.id == expense.expense_type_id),
            'UNKNOWN')
        data['value'] = expense.value
        response.append(data)
    return response, None


def update_candidate_monthly_expenses(candidate, expenses):
    prev_monthly_expense_assoc = CandidateMonthlyExpense.query.join(Candidate).filter(
        Candidate.id == candidate.id).all()

    # create new records first
    for data in expenses:
        expense_type = ExpenseType.query.filter_by(id=data.get('expense_type_id')).first()
        if expense_type:
            new_candidate_expense = CandidateMonthlyExpense()
            new_candidate_expense.candidate = candidate
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
        CandidateMonthlyExpense.query.filter(CandidateMonthlyExpense.candidate_id == candidate.id,
                                             CandidateMonthlyExpense.expense_id == expense_assoc.expense_id).delete()
        MonthlyExpense.query.filter_by(id=expense_assoc.expense_id).delete()
    save_changes()

    return {'message': 'Successfully updated monthly expenses'}, None


def update_candidate_addresses(candidate, addresses):
    for address in addresses:
        addr1 = '' if address['address1'] is None else address['address1']
        addr2 = address['address2'] if 'address2' in address else None
        zip_code = '' if address['zip_code'] is None else address['zip_code']
        city = '' if address['city'] is None else address['city']
        state = '' if address['state'] is None else address['state']

        from_date = datetime.datetime.utcnow()
        to_date = datetime.datetime.utcnow()
        if address['from_date'] != None and address['from_date'] != '':
            from_date = datetime.datetime.strptime(address['from_date'], "%Y-%m-%d")
        if address['to_date'] != None and address['to_date'] != '':
            to_date = datetime.datetime.strptime(address['to_date'], "%Y-%m-%d")
        # check already exists,if exists update
        # else create new one
        candid_address = Address.query.filter_by(candidate_id=candidate.id,
                                                 type=address['type']).first()
        if candid_address is None:
            candid_address = Address(candidate_id=candidate.id,
                                     address1=addr1,
                                     address2=addr2,
                                     zip_code=zip_code,
                                     city=city,
                                     state=state,
                                     from_date=from_date,
                                     to_date=to_date,
                                     type=address['type'])
            save_changes(candid_address)
        else:
            candid_address.address1 = addr1
            candid_address.address2 = addr2
            candid_address.zip_code = zip_code
            candid_address.city = city
            candid_address.state = state
            candid_address.from_date = from_date
            candid_address.to_date = to_date
            save_changes()

    return {'message': 'Successfully updated candidate addresses'}, None


def get_candidate_addresses(candidate):
    addresses = Address.query.filter_by(candidate_id=candidate.id).all()
    address_data = []
    for address in addresses:
        data = {}
        data['address1'] = address.address1
        data['address2'] = address.address2
        data['zip_code'] = address.zip_code
        data['city'] = address.city
        data['state'] = address.state
        data['from_date'] = address.from_date
        data['to_date'] = address.to_date
        data['type'] = address.type
        address_data.append(data)

    return address_data, None


def save_changes(data):
    db.session.add(data)
    db.session.commit()


def get_candidate_contact_numbers(candidate):
    contact_number_assoc = CandidateContactNumber.query.join(Candidate).filter(Candidate.id == candidate.id).all()
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


def update_candidate_contact_numbers(candidate, contact_numbers):
    prev_contact_numbers = CandidateContactNumber.query.join(Candidate).filter(Candidate.id == candidate.id).all()

    # create new records first
    for data in contact_numbers:
        phone_type = ContactNumberType.query.filter_by(id=data.get('phone_type_id')).first()
        if phone_type:
            new_candidate_number = CandidateContactNumber()
            new_candidate_number.candidate = candidate
            new_candidate_number.contact_number = ContactNumber(
                inserted_on=datetime.datetime.utcnow(),
                contact_number_type_id=data.get('phone_type_id'),
                phone_number=data.get('phone_number'),
                preferred=data.get('preferred')
            )
            db.session.add(new_candidate_number)
        else:
            return None, 'Invalid Contact Number Type'
    save_changes()

    # remove previous records
    for prev_number in prev_contact_numbers:
        CandidateContactNumber.query.filter(CandidateContactNumber.candidate_id == candidate.id,
                                            CandidateContactNumber.contact_number_id == prev_number.contact_number_id).delete()
        ContactNumber.query.filter_by(id=prev_number.contact_number_id).delete()
    save_changes()

    return {'message': 'Successfully updated contact numbers'}, None


def get_all_candidate_imports():
    return CandidateImport.query.all()


def get_all_candidates(search_query):
    search = "%{}%".format(search_query)
    return Candidate.query.filter_by(is_co_borrower=False) \
                          .filter(or_(Candidate.prequal_number.like(search) if search_query else True,
                                      Candidate.first_name.like(search) if search_query else True,
                                      Candidate.status.like(search) if search_query else True,
                                      Candidate.email.like(search) if search_query else True,
                                      Candidate.public_id.like(search) if search_query else True,
                                      Candidate.last_name.like(search) if search_query else True)) \
                          .outerjoin(CreditReportAccount).paginate(1, 50, False).items


def delete_candidates(ids):
    if ids is not None:
        candidates = Candidate.query.filter(Candidate.public_id.in_(ids)).all()
        for c in candidates:
            db.session.delete(c)
            db.session.commit()
        return


def get_candidates_count(q=None):
    if q is None or q == '':
        return Candidate.query.outerjoin(CreditReportAccount).count()
    else:
        search = "%{}%".format(q)
        return Candidate.query.filter_by(is_co_borrower=False).outerjoin(CreditReportAccount) \
                              .filter(or_(Candidate.first_name.ilike(search),
                                          Candidate.last_name.ilike(search),
                                          Candidate.prequal_number.ilike(search),
                                          Candidate.email.ilike(search),
                                          Candidate.public_id.ilike(search))).count()


def get_candidates_with_pagination(sort, order, page_number, limit):
    field = getattr(Candidate, sort)
    column_sorted = getattr(field, order)()
    return Candidate.query.filter_by(is_co_borrower=False).outerjoin(CreditReportAccount).order_by(column_sorted).paginate(page_number, limit,
                                                                                           False).items


def candidate_filter(limit=25, sort_col='id', order="asc",
                     pageno=1, search_fields=None, search_val="",
                     dt_fields=None, from_date=None, to_date=None,
                     numeric_fields=None):
    try:
        # sort
        sort = desc(sort_col) if order == 'desc' else asc(sort_col)
        total = 0

        query = Candidate.query.filter_by(is_co_borrower=False)\
                               .outerjoin(CandidateDisposition)\
                               .outerjoin(Campaign)\
                               .outerjoin(CreditReportAccount)\
                               .outerjoin(Address)\
                               .outerjoin(CandidateContactNumber)
        # search fields
        if search_fields is not None:
            _or_filts = []
            _and_filts = []

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

                # enumeration
                if 'status' in field:
                    rep = CandidateStatus.frm_text(e_val)
                    if rep is not None:
                        filt = (Candidate.status == rep)
                        # string fields
                else:
                    if 'disposition' in field:
                        column = getattr(CandidateDisposition, 'value', None)
                    elif 'campaign_name' in field:
                        column = getattr(Campaign, 'name', None)
                    else:
                        column = getattr(Candidate, field, None)
                    filt = column.ilike(search)

                # append to the filters
                if filt is not None:
                    if and_exp is True:
                        _and_filts.append(filt)
                    else:
                        _or_filts.append(filt)

            # check if filters are present
            if len(_or_filts) == 0 and len(_and_filts) == 0:
                return {"candidates": [], "page_number": pageno, "total_number_of_records": total, "limit": limit}
            else:
                if len(_or_filts) > 0:
                    query = query.filter(or_(*_or_filts))
                if len(_and_filts) > 0:
                    query = query.filter(and_(*_and_filts))

        # datetime fields
        if dt_fields is not None:
            for field in dt_fields:
                column = getattr(Candidate, field, None)
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

        candidates = query.items
        return {"candidates": candidates, "page_number": pageno, "total_number_of_records": total, "limit": limit}

    except Exception as err:
        app.logger.warning('candidate filter issue, {}'.format(str(err)))
        raise ValueError("Invalid filter query")


def get_candidate(public_id):
    candidate = Candidate.query.filter_by(public_id=public_id).join(CreditReportAccount).first()
    if candidate:
        return candidate
    else:
        return Candidate.query.filter_by(public_id=public_id).first()


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()


def save_new_candidate_import(data):
    new_candidate_import = CandidateImport(
        file=data['file_path'],
        public_id=str(uuid.uuid4()),
        inserted_on=datetime.datetime.utcnow(),
        updated_on=datetime.datetime.utcnow()
    )
    save_changes(new_candidate_import)
    db.session.refresh(new_candidate_import)
    return new_candidate_import


def convert_candidate_to_lead(candidate):
    client = create_client_from_candidate(candidate)
    # if coclient present, create
    if candidate.co_borrower:
      co_client =  create_client_from_candidate(candidate.co_borrower, ClientType.coclient)
      client.co_client = co_client
      db.session.commit()

    return client

def get_co_client(candidate):
    # fetch the co-client
    co_client = candidate.co_borrower
    if co_client is not None:
        return co_client
    else:
        return {
        }

def update_co_client(candidate, data):

    # required fields
    first_name = data.get('first_name')
    last_name  = data.get('last_name')
    email  = data.get('email')
    # optional fields
    mi = data.get('middle_initial').strip()
    dob = data.get('dob')
    ssn = data.get('ssn')
    language = data.get('language')


    co_client = candidate.co_borrower
    if co_client is None:
        # insert
        co_client = Candidate(public_id=str(uuid.uuid4()),
                              first_name=first_name,
                              last_name=last_name,
                              email=email,
                              middle_initial=mi,
                              dob=dob,
                              language=language,
                              estimated_debt=0,
                              is_co_borrower=True,
                              inserted_on=datetime.datetime.utcnow(),
                              debt3=0, debt15=0, debt2=0, debt215=0, debt3_2=0,
                              checkamt=0, spellamt="", debt315=0, year_interest=0,
                              total_interest=0, sav215=0, sav15=0, sav315=0)
        save_changes(co_client)
        candidate.co_borrower = co_client
        db.session.commit()

    else:
        #update
        co_client.first_name = first_name
        co_client.last_name = last_name
        co_client.email = email
        co_client.middle_initial = mi
        co_client.dob = dob
        co_client.language = language,
        db.session.commit()

    return co_client
