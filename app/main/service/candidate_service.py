import uuid
import datetime

from sqlalchemy import desc, asc, or_, and_
from app.main import db
from app.main.model.employment import Employment
from app.main.model import Frequency
from app.main.model.candidate import CandidateContactNumber, CandidateIncome, CandidateEmployment, CandidateMonthlyExpense
from app.main.model.contact_number import ContactNumber, ContactNumberType
from app.main.model.candidate import CandidateImport, Candidate
from app.main.model.credit_report_account import CreditReportAccount
from app.main.model.income import IncomeType, Income
from app.main.model.monthly_expense import ExpenseType, MonthlyExpense
from app.main.model.address import Address, AddressType
from app.main.service.client_service import create_client_from_candidate


def save_new_candidate(data):
    if data.get('phone') != None:
        exist_candidate = Candidate.query.filter(Candidate.phone==data.get('phone')).first()
    else:
        exist_candidate = Candidate.query.filter(and_(Candidate.first_name==data.get('first_name'),
         Candidate.last_name==data.get('last_name'),
         Candidate.email==data.get('email'),
        )).first()
    if exist_candidate != None:
        response_object = {
            'success': False,
            'status': 'failed',
            'message': 'This candidate already exists'
        }
        return response_object, 201
    new_candidate = Candidate(
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
        county=data.get('county'),
        estimated_debt=data.get('estimated_debt'),
        language=data.get('language'),
        phone=data.get('phone'),

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
    db.session.commit()

    new_address = Address(
        candidate_id = new_candidate.id,
        address1 = data.get('address'),
        zip_code = data.get('zip'),
        city = data.get('city'),
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
    prev_employments = CandidateEmployment.query.join(Candidate).filter(Candidate.id == candidate.id).all()

    # create new records first
    for data in employments:
        new_employment = CandidateEmployment()
        new_employment.candidate = candidate
        new_employment.employment = Employment(
            inserted_on=datetime.datetime.utcnow(),
            employer_name=data.get('employer_name'),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
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
        CandidateEmployment.query.filter(CandidateEmployment.candidate_id == candidate.id,
                                         CandidateEmployment.employment_id == prev_employment.employment_id).delete()
        Employment.query.filter_by(id=prev_employment.employment_id).delete()
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
            (expense_type.name for expense_type in expense_types if expense_type.id == expense.expense_type_id), 'UNKNOWN')
        data['value'] = expense.value
        response.append(data)
    return response, None


def update_candidate_monthly_expenses(candidate, expenses):
    prev_monthly_expense_assoc = CandidateMonthlyExpense.query.join(Candidate).filter(Candidate.id == candidate.id).all()

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
    prev_addresses = Address.query.filter_by(candidate_id=candidate.id).all()

    for address in addresses:
         new_address = Address(
            candidate_id=candidate.id,
            address1=address.get('address1'),
            address2=address.get('address2'),
            zip_code=address.get('zip_code'),
            city=address.get('city'),
            state=address.get('state'),
            from_date=datetime.datetime.strptime(address.get('from_date'), "%Y-%m-%d") if address.get('from_date') else None,
            to_date=datetime.datetime.strptime(address.get('to_date'), "%Y-%m-%d") if address.get('to_date') else None,
            type=address.get('type')
         )
         db.session.add(new_address)
    for prev_address in prev_addresses:
        Address.query.filter_by(id=prev_address.id).delete()
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
    return Candidate.query\
        .filter(or_(Candidate.prequal_number.like(search) if search_query else True,
            Candidate.first_name.like(search) if search_query else True,
            Candidate.status.like(search) if search_query else True,
            Candidate.address.like(search) if search_query else True,
            Candidate.county.like(search) if search_query else True,
            Candidate.state.like(search) if search_query else True,
            Candidate.city.like(search) if search_query else True,
            Candidate.phone.like(search) if search_query else True,
            Candidate.email.like(search) if search_query else True,
            Candidate.public_id.like(search) if search_query else True,
            Candidate.last_name.like(search) if search_query else True))\
        .outerjoin(CreditReportAccount).paginate(1, 50, False).items


def delete_candidates(ids):
     candidates = Candidate.query.filter(Candidate.public_id.in_(ids)).all()
     for c in candidates:
         db.session.delete(c)
         db.session.commit()
     return


def get_candidates_count():
    return Candidate.query.outerjoin(CreditReportAccount).count()


def get_candidates_with_pagination(sort, order, page_number, limit):
    field = getattr(Candidate, sort)
    column_sorted = getattr(field, order)()
    return Candidate.query.outerjoin(CreditReportAccount).order_by(column_sorted).paginate(page_number, limit, False).items

def candidate_search(q=None, limit=25, order="asc", sort_col='id', pageno=1): 
    sort = desc(sort_col) if order == 'desc' else asc(sort_col)
    search = "%{}%".format(q)
    if q is None:
        return Candidate.query.outerjoin(CreditReportAccount).order_by(sort).paginate(pageno, limit, False).items
    else:
        return Candidate.query.outerjoin(CreditReportAccount).filter(or_(Candidate.first_name.ilike(search), 
                   Candidate.last_name.ilike(search), Candidate.prequal_number.ilike(search))).order_by(sort).paginate(pageno, limit, False).items

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
    return create_client_from_candidate(candidate)
