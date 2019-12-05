import uuid
import datetime

from flask import current_app
from app.main import db
from app.main.model.candidate import CandidateImport, Candidate, CandidateContactNumber, CandidateEmployment
from app.main.model.employment import Employment
from app.main.model.contact_number import ContactNumber, ContactNumberType
from app.main.model.credit_report_account import CreditReportAccount


def save_new_candidate(data):
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
        zip4=data.get('zip'),
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

    save_changes(new_candidate)
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


def update_candidate_employments(candidate, employments):
    prev_employments = CandidateEmployment.query.join(Candidate).filter(Candidate.id == candidate.id).all()

    # create new records first
    for data in employments:
        new_employment = CandidateEmployment()
        new_employment.candidate = candidate
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
        CandidateEmployment.query.filter(CandidateEmployment.candidate_id == candidate.id,
                                            CandidateEmployment.employment_id == prev_employment.employment_id).delete()
        Employment.query.filter_by(id=prev_employment.employment_id).delete()
    save_changes()

    return {'message': 'Successfully updated employments'}, None


def get_candidate_contact_numbers(candidate):
    contact_number_assoc = CandidateContactNumber.query.join(Candidate).filter(Candidate.id == candidate.id).all()
    contact_numbers = [num.contact_number for num in contact_number_assoc]
    phone_types = ContactNumberType.query.filter(
        ContactNumberType.id.in_([num.contact_number_type_id for num in contact_numbers])).all()

    number_data = []
    for contact_number in contact_numbers:
        data = {}
        data['phone_type_id'] = contact_number.contact_number_type_id
        data['phone_type'] = next((phone_type.name for phone_type in phone_types), 'UNKNOWN')
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
    return CandidateImport.query.all();


def get_all_candidates():
    return Candidate.query.outerjoin(CreditReportAccount).paginate(1, 50, False).items


def get_candidate(public_id):
    candidate = Candidate.query.filter_by(public_id=public_id).join(CreditReportAccount).first()
    if candidate:
        return candidate
    else:
        return Candidate.query.filter_by(public_id=public_id).first()


def save_changes(data=None):
    db.session.add(data) if data else None
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
