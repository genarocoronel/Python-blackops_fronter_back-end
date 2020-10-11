import datetime
import uuid

import phonenumbers
from typing import List

from sqlalchemy import or_
from werkzeug.exceptions import NotFound

from app.main import db
from app.main.core import DEFAULT_PHONE_REGION
from app.main.core.helper import convert_to_boolean, is_boolean
from app.main.model.contact_number import ContactNumberType
from app.main.model.income import IncomeType
from app.main.model.candidate import CandidateDisposition
from app.main.model.client import ClientDisposition
from app.main.model.monthly_expense import ExpenseType
from app.main.model.pbx import PBXNumber, PBXSystem
from app.main.model.user import Department
from app.main.service.docproc_service import get_docproc_types, get_docproc_statuses


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


def get_pbx_systems(enabled=True):
    pbx_systems_stmt = PBXSystem.query.filter()
    if is_boolean(enabled):
        is_enabled = convert_to_boolean(enabled)
        pbx_systems_stmt = pbx_systems_stmt.filter_by(enabled=is_enabled)

    return pbx_systems_stmt.all()


def update_pbx_system(system_publuc_id:str, data):
    pbx_system = PBXSystem.query.filter_by(public_id=system_publuc_id).first()
    if not pbx_system :
        raise NotFound

    for attr in data:
        if hasattr(pbx_system , attr):
            setattr(pbx_system , attr, data.get(attr))

    db.session.add(pbx_system )
    db.session.commit()

    return pbx_system


def map_number_to_pbx_system(system_public_id:str, number_public_id:str):
    pbx_system = PBXSystem.query.filter_by(public_id=system_public_id).first()
    pbx_number = PBXNumber.query.filter_by(public_id=number_public_id).first()

    if pbx_system is None or pbx_number is None:
        raise NotFound

    pbx_number.pbx_system = pbx_system
    db.session.add(pbx_number)
    db.session.commit()


def delete_pbx_system(public_id:str):
    pbx_system = PBXSystem.query.filter_by(public_id=public_id).first()
    if pbx_system is None:
        raise NotFound

    db.session.delete(pbx_system)
    db.session.commit()


def get_registered_pbx_numbers(enabled=True, departments: List[Department] = None):
    pbx_numbers_stmt = PBXNumber.query.filter()
    if is_boolean(enabled):
        is_enabled = convert_to_boolean(enabled)
        pbx_numbers_stmt = pbx_numbers_stmt.filter_by(enabled=is_enabled)

    if departments:
        pbx_numbers_stmt = pbx_numbers_stmt.filter(or_(PBXNumber.department == department for department in departments))

    return [pbx.number for pbx in pbx_numbers_stmt.all()]


def get_registered_pbx_number_records(enabled=True):
    pbx_numbers_stmt = PBXNumber.query.filter()
    if is_boolean(enabled):
        is_enabled = convert_to_boolean(enabled)
        pbx_numbers_stmt = pbx_numbers_stmt.filter_by(enabled=is_enabled)

    return pbx_numbers_stmt.all()


def register_pbx_system(data):
    new_pbx_system = PBXSystem(
        public_id=str(uuid.uuid4()),
        name=data.get('name'),
        enabled=data.get('enabled'),
        inserted_on=datetime.datetime.utcnow(),
        updated_on=datetime.datetime.utcnow(),
    )
    db.session.add(new_pbx_system)
    db.session.commit()

    return new_pbx_system


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


def get_all_docproc_statuses():
    return get_docproc_statuses()
