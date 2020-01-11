import datetime
import uuid

from pytz import utc

from app.main import db
from app.main.model.candidate import CandidateDisposition

candidate_dispositions = [
    'Hung up in less than 1 minute',
    'Missed Call',
    'New Lead',
    'Missed Call-Attempting to contact',
    'Working Lead',
    'Working Lead-SmartCredit Issue',
    'Submitted',
    'Dead: Will not give personal info',
    'Dead: Locked out of smart credit',
    'Dead: Unfamiliar with Brand',
    'Dead: Going with another company',
    'Dead: Wrong Phone Number',
    'Dead: Could not reach',
    'Dead: No longer interested',
    'Dead: Take off list/Do not call',
    'Dead: No Invitation ID number',
    'Dead: No debt',
    'Dead: Wrong address',
    'Dead: Duplicate info',
    'Dead: Dead',
    'Dead: Stop Texting',
    'Dead: Old',
    'Dead: Fax',
    'Dead: Other',
]


def seed_candidate_disposition_values():
    for disposition in candidate_dispositions:
        existing_disposition_value = CandidateDisposition.query.filter_by(value=disposition).first()
        if not existing_disposition_value:
            new_disposition = CandidateDisposition(public_id=str(uuid.uuid4()), value=disposition,
                                                   inserted_on=datetime.datetime.now(tz=utc))
            db.session.add(new_disposition)
    db.session.commit()
