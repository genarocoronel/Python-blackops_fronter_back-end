import os
import unittest
import uuid
import subprocess

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask import current_app

from app import blueprint
from app import portal_blueprint
from app.main import create_app, db, wscomm
from app.main.core.auth import Auth
from app.main.model.credit_report_account import CreditReportAccount
from app.main.seed.admins import create_super_admin

from app.main.model import *
from app.main.model.user import User

from app.main.background.worker import run_worker
from app.main.seed.candidate_dispositions import seed_candidate_disposition_values
from app.main.seed.client_dispositions import seed_client_disposition_values
from app.main.seed.contact_number_types import seed_contact_number_types
from app.main.seed.expense_types import seed_expense_type_values
from app.main.seed.income_types import seed_income_types
from app.main.seed.rsign import seed_rsign_records
from app.main.seed.bank_account import seed_datax_validation_codes
from app.main.seed.checklist import seed_client_main_checklist
from app.main.seed.rac import seed_rac_roles
from app.main.seed.users_roles import seed_users_with_roles, seed_permissions
from app.main.tasks import jive_listener
from app.main.seed.team import seed_team_request_types
from app.main.seed.docproc import seed_docproc_types
from app.main.seed.collector import seed_debt_collectors
from app.main.seed.organization import seed_organizations
from app.main.seed.template import seed_templates
from app.main.seed.campaign import seed_pinnacle_phone_numbers
from app.main.seed.sales_board import seed_lead_distro_profile
from rq import job

environment = os.getenv('BOILERPLATE_ENV') or 'dev'
app = create_app(environment)
app.register_blueprint(blueprint, url_prefix='/api/v1')
app.register_blueprint(portal_blueprint, url_prefix='/portal-api/v1')
app.app_context().push()

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def worker(queue):
    # default worker queue is `default`
    run_worker(queue)


@manager.command
def worker_empty(queue):
    """ Empties the worker queue of ALL jobs """
    print(f'Total queued jobs: {current_app.queue.count}')
    current_app.queue.empty()
    print(f'Total queued jobs remaining: {current_app.queue.count}')


@manager.command
def worker_empty_failed(queue):
    """ Empties the worker queue of ALL failed jobs """
    failed_registry = current_app.queue.failed_job_registry
    print(f'Total failed jobs: {failed_registry.count}')
    for failed_job_id in failed_registry.get_job_ids():
        failed_job = current_app.queue.fetch_job(failed_job_id)
        print(failed_job_id, failed_job.exc_info)
        failed_job.delete()
    print(f'Total failed jobs remaining: {failed_registry.count}')


@manager.command
def worker_squak_failed(queue):
    """ Outputs ALL failed jobs """
    failed_registry = current_app.queue.failed_job_registry
    print(f'Total failed jobs: {failed_registry.count}')
    for failed_job_id in failed_registry.get_job_ids():
        failed_job = current_app.queue.fetch_job(failed_job_id)
        print(failed_job_id, failed_job.exc_info)


@manager.command
def seed():
    seed_rac_roles()

    super_admin_email = 'admin@localhost.com'
    super_admin_password = Auth.generate_password(20)
    if environment != 'prod' and environment != 'production':
        super_admin_password = 'password'
        seed_users_with_roles()
        seed_pinnacle_phone_numbers()

    create_super_admin(email=super_admin_email, password=super_admin_password)
    seed_permissions()
    seed_candidate_disposition_values()
    seed_client_disposition_values()
    seed_contact_number_types()
    seed_expense_type_values()
    seed_income_types()
    seed_rsign_records()
    seed_datax_validation_codes()
    seed_client_main_checklist()
    seed_team_request_types()
    seed_docproc_types()
    seed_debt_collectors()
    seed_organizations()
    seed_templates()
    seed_pinnacle_phone_numbers()
    seed_lead_distro_profile() 


## launching development server
## uses eventlet library for websocket support
## Werkzueg run is replaced with SocketIO run  
@manager.command
def run():
    wscomm.run(app, host='0.0.0.0', port=5000, log_output=True)


@manager.command
def encrypt_string(password):
    print(current_app.cipher.encrypt(password.encode()).decode("utf-8"))


@manager.command
def kron():
    subprocess.run(["python", "-m", "app.main.scheduler", "--url", app.config['REDIS_URL']])



@manager.command
def comms_listener():
    jive_listener.run()


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

from app.test.regress import RegressionTest
@manager.option('--host', help='Host Name')
@manager.option('--role', help='User role')
@manager.option('--uname', help='Username')
@manager.option('--pswd', help='Password')
@manager.command
def regress(host, role, uname, pswd):
    test = RegressionTest(host)
    test.run(role=role, uname=uname, pswd=pswd)

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
