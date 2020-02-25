import os
import unittest
import uuid
import subprocess

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask import current_app

from app import blueprint
from app.main import create_app, db
from app.main.seed.admins import create_super_admin

from app.main.background.worker import run_worker
from app.main.model.notes import Note
from app.main.model.sms import SMSMessage
from app.main.model.campaign import Campaign
from app.main.model.docsign import DocusignTemplate, DocusignSession, DocusignSignature
from app.main.model.debt_payment import DebtEftStatus, DebtPaymentSchedule, DebtPaymentTransaction, DebtPaymentContract
from app.main.model.client import Client
from app.main.model.client_call import ClientCall
from app.main.model.contact_number import ContactNumberType, ContactNumber
from app.main.model.address import AddressType, Address
from app.main.model.income import IncomeType, Income
from app.main.model.monthly_expense import ExpenseType, MonthlyExpense
from app.main.model.credit_report_account import CreditReportAccount
from app.main.seed.candidate_dispositions import seed_candidate_disposition_values
from app.main.seed.client_dispositions import seed_client_disposition_values
from app.main.seed.contact_number_types import seed_contact_number_types
from app.main.seed.expense_types import seed_expense_type_values
from app.main.seed.income_types import seed_income_types
from app.main.seed.rsign import seed_rsign_records
from app.main.seed.bank_account import seed_datax_validation_codes

app = create_app(os.getenv('BOILERPLATE_ENV') or 'dev')
app.register_blueprint(blueprint, url_prefix='/api/v1')
app.app_context().push()

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def worker(queue):
    # default worker queue is `default`
    run_worker(queue)

@manager.command
def seed():
    create_super_admin()
    seed_candidate_disposition_values()
    seed_client_disposition_values()
    seed_contact_number_types()
    seed_expense_type_values()
    seed_income_types()
    seed_rsign_records()
    seed_datax_validation_codes()


@manager.command
def run():
    app.run(host='0.0.0.0')


@manager.command
def encrypt_string(password):
    print(current_app.cipher.encrypt(password.encode()).decode("utf-8"))


# kron
@manager.command
def kron():
    subprocess.run(["python", "-m", "app.main.scheduler", "--url", app.config['REDIS_URL']])
    

@manager.option('-t', '--client_type', help='Client Type (candidate, client)')
@manager.option('-i', '--client_id', help='Client ID')
@manager.option('-e', '--email', help='Account email')
@manager.option('-p', '--password', help='Account password')
def create_credit_account(client_type, client_id, email, password):
    """ create credit report account and map it to either candidate or client tables """
    credit_report_account = CreditReportAccount(
        public_id=str(uuid.uuid4()),
        tracking_token=str(uuid.uuid4()),
        email=email,
        password=password
    )
    if 'lead' == client_type.lower():
        credit_report_account.client_id = client_id
    elif 'candidate' == client_type.lower():
        credit_report_account.candidate_id = client_id

    db.session.add(credit_report_account)
    db.session.commit()


@manager.command
def test():
    """Runs the unit tests."""
    tests = unittest.TestLoader().discover('app/test', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    manager.run()
