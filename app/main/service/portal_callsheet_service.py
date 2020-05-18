import uuid
import datetime
from flask import g

from app.main import db
from app.main.core.errors import BadRequestError
from app.main.model.portal_callsheet import PortalCallsheet
from app.main.service.portal_user_service import get_portal_user_by_pubid, get_portal_user_by_id



def get_callsheets_for_portal_user():
    pass
    callsheets = []
    puser = get_portal_user_by_pubid(g.current_portal_user['public_id'])
    if puser:
        callsheet_records = PortalCallsheet.query.filter_by(portal_user_id=puser.id).all()

        if callsheet_records:
            for callsheet_item in callsheet_records:
                tmp_callsheet = synth_callsheet(callsheet_item)
                callsheets.append(tmp_callsheet)

    return callsheets


def create_callsheet(data):
    callsheet_response = None

    puser = get_portal_user_by_pubid(g.current_portal_user['public_id'])
    if puser:
        callsheet = PortalCallsheet(
            public_id = str(uuid.uuid4()),
            portal_user_id = puser.id,
            is_orig_creditor = data['is_orig_creditor'] if 'is_orig_creditor' in data else False,
            is_hardship_call = data['is_hardship_call'] if 'is_hardship_call' in data else False,
            debt_name = data['debt_name'],
            creditor_name = data['creditor_name'],
            collector_name = data['collector_name'],
            received_from_phone_number = data['received_from_phone_number'],
            received_on_phone_type = data['received_on_phone_type'],
            notes = data['notes'] if 'notes' in data else None,
            inserted_on = datetime.datetime.utcnow(),
            updated_on = datetime.datetime.utcnow(),
        )
        _save_changes(callsheet)
        callsheet_response = synth_callsheet(callsheet)

    return callsheet_response


def synth_callsheet(callsheet):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    puser = get_portal_user_by_id(callsheet.portal_user_id)
    
    callsheet_synth = {
        'public_id': callsheet.public_id,
        'portal_user_public_id': puser.public_id,
        'is_orig_creditor': callsheet.is_orig_creditor,
        'is_hardship_call': callsheet.is_hardship_call,
        'debt_name': callsheet.debt_name,
        'creditor_name': callsheet.creditor_name,
        'collector_name': callsheet.collector_name,
        'received_from_phone_number': callsheet.received_from_phone_number,
        'received_on_phone_type': callsheet.received_on_phone_type,
        'notes': callsheet.notes,
        'is_file_attached': callsheet.is_file_attached,
        'inserted_on': callsheet.inserted_on.strftime(datetime_format),
        'updated_on': callsheet.inserted_on.strftime(datetime_format)
    }

    return callsheet_synth


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()