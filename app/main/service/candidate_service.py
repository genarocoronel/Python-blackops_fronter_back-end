import uuid
import datetime

from app.main import db
from app.main.model.candidate import CandidateImport, Candidate


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


def get_all_candidate_imports():
    return CandidateImport.query.all();


def get_all_candidates():
    return Candidate.query.paginate(1, 50, False).items


def get_candidate(public_id):
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
