import datetime
import uuid

from app.main.model.docproc import DocprocType
from app.main import db


def seed_docproc_types():
    """ Seeds Doc Processing Types """
    types_seed = [
        {'name': 'Summons'},
        {'name': 'Collection Letter'},
        {'name': 'ID'},
        {'name': 'Voided Check'},
        {'name': 'Address Verification'},
        {'name': 'Validation Receipt'},
        {'name': 'Validation Response'},
        {'name': 'Signature'},
        {'name': 'Cancellation Request'},
        {'name': 'Amendment Signed'},
        {'name': 'Enrollment'},
        {'name': 'Account Settlement'},
        {'name': 'Credit Reports'},
        {'name': '3B Credit Report'},
        {'name': '1B Credit Report'},
        {'name': 'Dispute Document'},
        {'name': 'Uncle Letter'},
        {'name': 'Not Legible'},
        {'name': 'Budget'},
        {'name': 'Call Log'},
        {'name': 'Post Apt Mssg'},
        {'name': 'Smart Credit Report'},
        {'name': 'OC Correspondence'},
        {'name': '3P Correspondence'},
        {'name': 'Delete'},
        {'name': 'Credit Bureau Response'},
        {'name': 'Other'}
    ]

    for type_item in types_seed:
        existing_type = DocprocType.query.filter_by(name=type_item['name']).first()
        if not existing_type:
            new_type = DocprocType(
                public_id= str(uuid.uuid4()),
                name= type_item['name'],
                inserted_on= datetime.datetime.utcnow(),
                updated_on= datetime.datetime.utcnow()
            )
            db.session.add(new_type)

    db.session.commit()
    