import uuid

from app.main import db
from app.main.core.errors import NoDuplicateAllowed, BadRequestError, NotFoundError
from app.main.core.auth import Auth
from app.main.core.types import CustomerType
from app.main.model.candidate import Candidate
from app.main.model.client import Client
from app.main.model.credit_report_account import CreditReportAccount, CreditReportSignupStatus, CreditReportData
from app.main.service.smartcredit_service import (start_signup_session, create_customer, update_customer, 
    fetch_security_questions, get_id_verification_question, answer_id_verification_questions, 
    complete_credit_account_signup, activate_smart_credit_insurance)
from flask import current_app as app


def creport_account_signup(request_data: dict, internal_customer, customer_type: CustomerType):
    """ Signs up a Candidate or Lead (Client) for a Credit Report Account """
    app.logger.info("Signing up for Credit Report Account")
    if not internal_customer.email:
        raise BadRequestError(f'Cannot create credit report account for Customer with ID {internal_customer.public_id} without an email.')

    # 1. First ensure a Credit Report account doesn't exist
    existing_account = internal_customer.credit_report_account
    if existing_account and existing_account.status == CreditReportSignupStatus.ACCOUNT_CREATED:
        raise NoDuplicateAllowed(f'A credit report account already exists with status {existing_account.status.value} for client with ID {internal_customer.public_id}')
    
    # 2. Initiate a signup session with external service
    external_signup_session = start_signup_session()

    # 3. Create new account record with status ACCOUNT_CREATED
    if customer_type == CustomerType.CANDIDATE:
        creport_acc = create_creport_account_for_candidate(external_signup_session, internal_customer, 
                                                        CreditReportSignupStatus.INITIATING_SIGNUP)
    else:
        creport_acc = create_creport_account_for_client(external_signup_session, internal_customer, 
                                                        CreditReportSignupStatus.INITIATING_SIGNUP)

    # 4. Create a (external) SCredit customer to represent our own Client
    # We generate password on backend so Users don't have direct access to SCredit account credentials
    # for any given Lead/Client
    app.logger.info("Attempting to create customer with external Provider")
    password = Auth.generate_password()
    request_data.update({'password': password})
    request_data['email'] = creport_acc.email
    external_customer_info = create_customer(request_data, creport_acc.tracking_token,
                                        sponsor_code=app.smart_credit_sponsor_code)

    creport_acc.password = password
    creport_acc.customer_token = external_customer_info.get('customer_token')
    creport_acc.financial_obligation_met = external_customer_info.get('is_financial_obligation_met')
    creport_acc.plan_type = external_customer_info.get('plan_type')
    creport_acc.status = CreditReportSignupStatus.ACCOUNT_CREATED
    update_credit_report_account(creport_acc, None)

    return creport_acc


def create_creport_account_for_candidate(external_acc_session, candidate: Candidate, 
                                        status: CreditReportSignupStatus = None):
    """ Creates Credit Report Account for Candidate """
    app.logger.info(f"Saving new Credit Report Account for Candidate with ID {candidate.public_id}")
    account = CreditReportAccount.query.filter_by(customer_token=external_acc_session.get('customer_token'),
                                                  tracking_token=external_acc_session.get('tracking_token')).first()
    if account:
        raise NoDuplicateAllowed(f'Credit Report Account already exists for candidate with ID {candidate.public_id}')
    
    new_account = CreditReportAccount(
        public_id=str(uuid.uuid4()),
        customer_token=external_acc_session.get('customer_token'),
        provider=external_acc_session.get('provider'),
        tracking_token=external_acc_session.get('tracking_token') or external_acc_session.get('trackingToken'),
        plan_type=external_acc_session.get('plan_type'),
        financial_obligation_met=external_acc_session.get('financial_obligation_met'),
        status=status or CreditReportSignupStatus.INITIATING_SIGNUP,
        candidate=candidate,
        email=candidate.email
    )
    save_changes(new_account)

    return new_account        


def create_creport_account_for_client(external_acc_session, client: Client, status: CreditReportSignupStatus = None):
    """ Creates Credit Report Account for Client (Lead) """
    app.logger.info(f"Saving new Credit Report Account for Lead/Client with ID {client.public_id}")
    account = CreditReportAccount.query.filter_by(customer_token=external_acc_session.get('customer_token'),
                                                  tracking_token=external_acc_session.get('tracking_token')).first()
    if account:
        raise NoDuplicateAllowed(f'Credit Report Account already exists for Lead with ID {client.public_id}')
    
    new_account = CreditReportAccount(
        public_id=str(uuid.uuid4()),
        customer_token=external_acc_session.get('customer_token'),
        provider=external_acc_session.get('provider'),
        tracking_token=external_acc_session.get('tracking_token') or external_acc_session.get('trackingToken'),
        plan_type=external_acc_session.get('plan_type'),
        financial_obligation_met=external_acc_session.get('financial_obligation_met'),
        status=status or CreditReportSignupStatus.INITIATING_SIGNUP,
        client=client,
        email=client.email
    )
    save_changes(new_account)
    
    return new_account


def get_verification_questions(creport_account):
    """ Gets remote verification questions for Credit Account """
    app.logger.info("Fetching identify verification questions from remote service.")
    questions = get_id_verification_question(creport_account.customer_token, creport_account.tracking_token)
    creport_account.status = CreditReportSignupStatus.ACCOUNT_VALIDATING
    update_credit_report_account(creport_account, None)
    return questions


def answer_verification_questions(creport_account, questions_data):
    """ Submits Identity verification questions with remote service """
    app.logger.info("Submitting identity verification questions with remote service")
    answer_id_verification_questions(questions_data, creport_account.customer_token, creport_account.tracking_token)
    creport_account.status = CreditReportSignupStatus.ACCOUNT_VALIDATED
    update_credit_report_account(creport_account, None)
    return creport_account

def get_security_questions(creport_account):
    """ Gets remote security questions """
    app.logger.info("Fetching security questions from remote service.")
    return fetch_security_questions(creport_account.tracking_token)


def complete_signup(creport_account):
    """ Completes remote credit account signup """
    complete_credit_account_signup(creport_account.customer_token, creport_account.tracking_token)
    creport_account.status = CreditReportSignupStatus.FULL_MEMBER
    update_credit_report_account(creport_account, None)
    return creport_account


def get_account_password(creport_account):
    """ Gets the password for a Customer's Credit Account """
    return app.cipher.decrypt(creport_account.password.encode()).decode()


def update_credit_report_account(creport_account: CreditReportAccount, external_customer_data: None):
    app.logger.info(f"Updating Credit Report Account with ID {creport_account.public_id}")
    if (external_customer_data):
        if not external_customer_data['ip_address']:
            raise Exception('Cannot update customer with remote service without specifying IP')
        
        update_customer(creport_account.customer_token, external_customer_data, creport_account.tracking_token)
        creport_account.status = CreditReportSignupStatus.ACCOUNT_VALIDATING

    existing_account = CreditReportAccount.query.filter_by(id=creport_account.id).first()  # type: CreditReportAccount
    if not existing_account:
        raise NotFoundError(f'Credit Report Account with specified ID {creport_account.id} does not exist')

    existing_account.customer_token = creport_account.customer_token
    existing_account.plan_type = creport_account.plan_type
    existing_account.financial_obligation_met = creport_account.financial_obligation_met
    existing_account.status = creport_account.status
    save_changes(existing_account)

    return existing_account


def register_fraud_insurance(creport_account):
    """ Registers a Customer for Fraud Insurance with remote service provider """
    password = app.cipher.decrypt(creport_account.password).decode()
    result = activate_smart_credit_insurance(creport_account.email, password)
    creport_account.registered_fraud_insurance = True
    update_credit_report_account(creport_account, None)

    return result


def pull_credit_report(creport_account):
    """ Pulls Credit Report and scrapes Debts """
    app.logger.info("Pulling Credit Report")
    if not creport_account.registered_fraud_insurance:
        app.logger.info("Also registering for fraud insurance with external service")
        password = app.cipher.decrypt(creport_account.password.encode()).decode()
        activate_smart_credit_insurance(creport_account.email, password)

    creport_account.registered_fraud_insurance = True
    update_credit_report_account(creport_account, None)
    app.logger.info("Creating job to import Credit Report debts for Lead")
    scrape_credit_report(credit_report_account, 'Pulling credit report debts for Lead')


def get_all_credit_report_accounts():
    return CreditReportAccount.query.all()


def get_credit_report_account(public_id):
    return CreditReportAccount.query.filter_by(public_id=public_id).first()


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()
