import uuid

from app.main import db
from app.main.model.candidate import Candidate
from app.main.model.credit_report_account import CreditReportAccount,\
    CreditReportSignupStatus, CreditReportData
from app.main.model.task import ScrapeTask
from flask import jsonify


def get_report_data(candidate_public_id):
    data = CreditReportData.query.filter_by(candidate_id=candidate_public_id).all()
    return data


def save_new_credit_report_account(data, candidate: Candidate, status: CreditReportSignupStatus = None):
    account = CreditReportAccount.query.filter_by(customer_token=data.get('customer_token'),
                                                  tracking_token=data.get('tracking_token')).first()
    if not account:
        new_account = CreditReportAccount(
            public_id=str(uuid.uuid4()),
            customer_token=data.get('customer_token'),
            provider=data.get('provider'),
            tracking_token=data.get('tracking_token') or data.get('trackingToken'),
            plan_type=data.get('plan_type'),
            financial_obligation_met=data.get('financial_obligation_met'),
            status=status or CreditReportSignupStatus.INITIATING_SIGNUP,
            candidate=candidate
        )
        save_changes(new_account)
        return new_account
    else:
        raise Exception('Credit Report Account already exists')


def update_credit_report_account(account: CreditReportAccount):
    existing_account = CreditReportAccount.query.filter_by(id=account.id).first()  # type: CreditReportAccount
    if existing_account:
        existing_account.customer_token = account.customer_token
        existing_account.plan_type = account.plan_type
        existing_account.financial_obligation_met = account.financial_obligation_met
        existing_account.status = account.status
        save_changes(existing_account)
    else:
        raise Exception(f'Credit Report Account {account.id} does not exist')


def get_all_credit_report_accounts():
    return CreditReportAccount.query.all()


def get_credit_report_account(public_id):
    return CreditReportAccount.query.filter_by(public_id=public_id).first()


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()
