import os
import unittest

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from app import blueprint
from app.main import create_app, db
from app.main.seed.admins import create_super_admin

from app.main.background.worker import run_worker
from app.main.model.sms import SMSMessage
from app.main.model.campaign import Campaign
from app.main.model.docsign import DocusignTemplate, DocusignSignature
from app.main.model.client import Client
from app.main.model.contact_number import ContactNumberType, ContactNumber
from app.main.model.address import AddressType, Address
from app.main.model.income import IncomeType, Income
from app.main.model.monthly_expense import ExpenseType, MonthlyExpense
from app.main.model.client import Client
from app.main.model.credit_report_account import CreditReportData


app = create_app(os.getenv('BOILERPLATE_ENV') or 'dev')
app.register_blueprint(blueprint, url_prefix='/api/v1')

app.app_context().push()

manager = Manager(app)

migrate = Migrate(app, db)

manager.add_command('db', MigrateCommand)


@manager.command
def candidate_parser_worker():
    run_worker('candidate-upload-tasks')


@manager.command
def credit_report_worker():
    run_worker('credit-report-scrape-tasks')


@manager.command
def mailer_file_worker():
    run_worker('mailer-file-tasks')


@manager.command
def seed():
    create_super_admin()


@manager.command
def run():
    app.run(host='0.0.0.0')


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
