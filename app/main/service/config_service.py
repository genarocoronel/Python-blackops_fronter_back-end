import datetime
import uuid

import phonenumbers
from typing import List

from sqlalchemy import or_
from werkzeug.exceptions import NotFound

from app.main import db
from app.main.model.contact_number import ContactNumberType
from app.main.model.income import IncomeType
from app.main.model.candidate import CandidateDisposition
from app.main.model.client import ClientDisposition
from app.main.model.monthly_expense import ExpenseType
from app.main.model.pbx import PBXNumber
from app.main.model.user import Department
from app.main.service.docproc_service import get_docproc_types

DEFAULT_PHONE_REGION = 'US'


def get_contact_number_types():
    return ContactNumberType.query.all()


def get_income_types():
    return IncomeType.query.all()


def get_expense_types():
    return ExpenseType.query.all()


def get_all_candidates_dispositions():
    return CandidateDisposition.query.filter_by().all()


def get_all_clients_dispositions():
    return ClientDisposition.query.filter_by().all()


def get_registered_pbx_numbers(enabled=True, departments: List[Department] = None):
    pbx_numbers_stmt = PBXNumber.query.filter_by(enabled=enabled)
    if departments:
        pbx_numbers_stmt = pbx_numbers_stmt.filter(or_(PBXNumber.department == department for department in departments))

    return [pbx.number for pbx in pbx_numbers_stmt.all()]


def get_registered_pbx_number_records(enabled=True):
    return PBXNumber.query.filter_by(enabled=enabled).all()


def register_pbx_number(data):
    new_pbx_number = PBXNumber(
        public_id=str(uuid.uuid4()),
        number=phonenumbers.parse(data.get('number'), DEFAULT_PHONE_REGION).national_number,
        enabled=data.get('enabled'),
        department=data.get('department'),
        inserted_on=datetime.datetime.utcnow(),
        updated_on=datetime.datetime.utcnow(),
    )

    db.session.add(new_pbx_number)
    db.session.commit()

    return new_pbx_number


def update_pbx_number(public_id, data):
    pbx_number = PBXNumber.query.filter_by(public_id=public_id).first()
    if not pbx_number:
        raise NotFound

    for attr in data:
        if hasattr(pbx_number, attr):
            setattr(pbx_number, attr, data.get(attr))

    db.session.add(pbx_number)
    db.session.commit()

    return pbx_number


def get_all_docproc_types():
    return get_docproc_types()
