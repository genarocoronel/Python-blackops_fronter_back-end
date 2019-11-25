import enum
from flask import current_app
import datetime
from app.main import db
from app.main.model.task import ScrapeTask


class CreditReportSignupStatus(enum.Enum):
    INITIATING_SIGNUP = 'initiating_signup'
    ACCOUNT_CREATED = 'account_created'
    ACCOUNT_VALIDATING = 'account_validating'
    ACCOUNT_VALIDATED = 'account_validated'
    FULL_MEMBER = 'full_member'


class CreditReportSpiderStatus(enum.Enum):
    CREATED = 'created'
    RUNNING = 'running'
    COMPLETED = 'completed'
    ERROR = 'error'


class CreditReportAccount(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "credit_report_accounts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    public_id = db.Column(db.String(100), unique=True)
    provider = db.Column(db.String(50), nullable=False, default='Smart Credit')
    customer_token = db.Column(db.String(), unique=True, nullable=True)
    tracking_token = db.Column(db.String(100), nullable=False)
    plan_type = db.Column(db.String(50), nullable=True)
    financial_obligation_met = db.Column(db.Boolean, nullable=True)
    _password_enc = db.Column('password_enc', db.String(128), nullable=True)
    status = db.Column(db.Enum(CreditReportSignupStatus), nullable=False,
                       default=CreditReportSignupStatus.INITIATING_SIGNUP)

    @property
    def password(self):
        return self._password_enc

    @password.setter
    def password(self, password):
        self._password_enc = current_app.cipher.encrypt(password.encode())


class CreditReportData(db.Model):
    """ Db Model for storing candidate report data """
    __tablename__ = "credit_report_data"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    public_id = db.Column(db.String(100), unique=True)
    debt_name = db.Column(db.String(100), nullable=True)
    creditor = db.Column(db.String(100), nullable=True)
    ecoa = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(25), nullable=True)
    account_type = db.Column(db.String(100), nullable=True)
    push = db.Column(db.Boolean, nullable=True, default=False)
    last_collector = db.Column(db.String(100), nullable=True)
    collector_account = db.Column(db.String(100), nullable=True)
    last_debt_status = db.Column(db.String(100), nullable=True)
    bureaus = db.Column(db.String(100), nullable=True)
    days_delinquent = db.Column(db.String(20), nullable=True)
    balance_original = db.Column(db.String(20), nullable=True)
    payment_amount = db.Column(db.String(20), nullable=True)
    credit_limit = db.Column(db.String(20), nullable=True)
    graduation = db.Column(db.String(30), nullable=True)
    last_update = db.Column(db.DateTime, nullable=True)

    def launch_spider(self, name, description, candidate_public_id, *args, **kwargs):
        rq_job = current_app.spider_queue.enqueue(
            'app.main.scrape.credit_report_spider.' + name,
            candidate_public_id,
            *args,
            **kwargs
        )
        task = ScrapeTask(
            id=rq_job.get_id(),
            name=name,
            description=description,
            candidate_id=candidate_public_id,
            inserted_on=datetime.datetime.utcnow(),
            updated_on=datetime.datetime.utcnow()
        )
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return ScrapeTask.query.filter_by(
            user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return ScrapeTask.query.filter_by(
            name=name, user=self, complete=False).first()
