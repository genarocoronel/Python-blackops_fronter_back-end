import uuid
import datetime
from flask import g

from app.main import db
from app.main.core.errors import BadRequestError
from app.main.model.portal_callsheet import PortalCallsheet
from app.main.model.docproc import DocprocChannel, DocprocType
from app.main.service.docproc_service import create_doc_manual, attach_file_to_doc, get_doctype_by_name, stream_doc_file
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


def get_callsheet_by_pubid(public_id):
    """ Gets a Callsheet by Public ID """
    return PortalCallsheet.query.filter_by(public_id=public_id).first()


def create_callsheet(data):
    callsheet_response = None

    puser = get_portal_user_by_pubid(g.current_portal_user['public_id'])
    if puser:
        callsheet = PortalCallsheet(
            public_id = str(uuid.uuid4()),
            portal_user_id = puser.id,
            callsheet_date = data['callsheet_date'],
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


def attach_file_to_callsheet(callsheet, file):
    """ Attaches a File to a Callsheet via Docproc """
    if not callsheet.docproc:
        doc_type = get_doctype_by_name('Other')
        doc_data = {
            'doc_name': 'Portal Callsheet Doc',
            'source_channel': DocprocChannel.PORTAL.value,
            'debt_name': callsheet.debt_name,
            'creditor_name': callsheet.creditor_name,
            'collector_name': callsheet.collector_name,
            'type': {'public_id': doc_type.public_id}
        }

        doc = create_doc_manual(doc_data, None, True)

        callsheet.docproc = doc
        callsheet.is_file_attached = True
        _save_changes(callsheet)
    
    updated_doc = attach_file_to_doc(callsheet.docproc, file)
    callsheet_synth = synth_callsheet(callsheet)
    callsheet_synth['docproc'] = updated_doc

    return callsheet_synth


def stream_callsheet_file(doc):
    return stream_doc_file(doc)


def synth_callsheet(callsheet):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    puser = get_portal_user_by_id(callsheet.portal_user_id)
    
    callsheet_synth = {
        'public_id': callsheet.public_id,
        'callsheet_date': callsheet.callsheet_date.strftime(datetime_format),
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
        'docproc': None,
        'inserted_on': callsheet.inserted_on.strftime(datetime_format),
        'updated_on': callsheet.inserted_on.strftime(datetime_format)
    }

    return callsheet_synth


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()