import datetime
import uuid

from .. import db
from flask import current_app as app

from app.main.model.audit import Auditable, Audit


def record(auditable, auditable_subject_pubid, action, requestor_username,
            message=None, is_internal=True):
    """ Records an Audit item """
    if _is_valid_auditable(auditable):

        new_audit = Audit(
            public_id=str(uuid.uuid4()),
            auditable=auditable,
            auditable_subject_pubid=auditable_subject_pubid,
            action=action,
            requestor_username=requestor_username,
            message=message,
            is_internal=is_internal,
            inserted_on=datetime.datetime.utcnow()
        )
        _save_changes(new_audit)


def _is_valid_auditable(auditable):
    auditables = set(item.value for item in Auditable)
    return auditable in auditables


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()