import uuid
import datetime

from sqlalchemy import desc

from app.main import db
from app.main.model.audit import Audit


def get_audit_by_object_id(auditable_subject_pubid, auditable):
    return Audit.query.filter_by(
        auditable=auditable.value, 
        auditable_subject_pubid=auditable_subject_pubid,
        is_internal=False).all()


def get_last_audit_item(auditable_subject_pubid, auditable):
    return Audit.query.filter_by(
        auditable=auditable.value, 
        auditable_subject_pubid=auditable_subject_pubid,
        is_internal=False).order_by(db.desc(Audit.id)).first()


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()