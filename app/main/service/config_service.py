from app.main.model.contact_number import ContactNumberType
from app.main.model.income import IncomeType
from app.main.model.candidate import CandidateDisposition
from app.main.model.client import ClientDisposition
from app.main.model.monthly_expense import ExpenseType
from app.main.model.pbx import PBXNumber
from app.main.model.docproc import DocprocType
from app.main.service.docproc_service import get_docproc_types


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


def get_registered_pbx_numbers(enabled=True):
    return [pbx.number for pbx in PBXNumber.query.filter_by(enabled=enabled).all()]


def get_all_docproc_types():
    return get_docproc_types()
