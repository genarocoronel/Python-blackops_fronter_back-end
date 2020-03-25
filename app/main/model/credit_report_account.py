import enum
from flask import current_app
from app.main import db
from app.main.model.task import ScrapeTask


class CreditReportSignupStatus(enum.Enum):
    INITIATING_SIGNUP = 'initiating_signup'  # represents a request to create account with third-party vendor
    ACCOUNT_CREATED = 'account_created'  # represents initial account defined/created with third-party vendor
    ACCOUNT_VALIDATING = 'account_validating'  # represents any step in account creation requiring validation
    ACCOUNT_VALIDATED = 'account_validated'  # represents any account validation being complete
    FULL_MEMBER = 'full_member'  # represents account created with third-party vendor; awaiting additional steps
    FULL_MEMBER_LOGIN = 'full_member_login'  # represents account creation complete including any additional steps

class CreditReportDataAccountType(enum.Enum):
    CREDIT_CARD = 'credit_card'  # represents a request to create account with third-party vendor
    MEDICAL_BILL = 'medical_bill'  # represents initial account defined/created with third-party vendor
    LINE_OF_CREDIT = 'line_of_credit'  # represents any step in account creation requiring validation
    PERSONAL_LOAN = 'personal_loan'  # represents any account validation being complete
    UNSECURED_DEBT = 'unsecured_debt'  # represents account created with third-party vendor; awaiting additional steps
    OTHER = 'other'  # represents account creation complete including any additional steps

class CreditReportAccount(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "credit_report_accounts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)

    # foreign keys
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='fk_client'))

    # fields
    provider = db.Column(db.String(50), nullable=False, default='Smart Credit')
    customer_token = db.Column(db.String(), unique=True, nullable=True)
    tracking_token = db.Column(db.String(100), nullable=False)
    plan_type = db.Column(db.String(50), nullable=True)
    financial_obligation_met = db.Column(db.Boolean, nullable=True)
    _password_enc = db.Column('password_enc', db.String(128), nullable=True)
    status = db.Column(db.Enum(CreditReportSignupStatus), nullable=False,
                       default=CreditReportSignupStatus.INITIATING_SIGNUP)
    email = db.Column(db.String(100), nullable=True, unique=True)
    registered_fraud_insurance = db.Column(db.Boolean, nullable=False, default=False)

    # move this to appropriate table, if needed
    # FICO score
    fico = db.Column(db.Integer, nullable=True)

    # relationship
    records = db.relationship("CreditReportData", backref="credit_report_accounts") 

    @property
    def password(self):
        return self._password_enc

    @password.setter
    def password(self, password):
        self._password_enc = current_app.cipher.encrypt(password.encode()).decode()

    def launch_spider(self, name, description, *args, **kwargs):
        rq_job = current_app.queue.enqueue(
            'app.main.tasks.credit_report.' + name,
            self.id,
            *args,
            **kwargs
        )
        task = ScrapeTask(id=rq_job.get_id(), name='credit_report_spider', account_id=self.id)
        db.session.add(task)
        return task


class CreditReportData(db.Model):
    """ Db Model for storing candidate report data """
    __tablename__ = "credit_report_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    last_update = db.Column(db.DateTime, nullable=True)

    # foreign keys
    account_id = db.Column(db.Integer, db.ForeignKey('credit_report_accounts.id', name='fk_credit_report_data'))

    # fields
    debt_name = db.Column(db.String(100), nullable=True)
    creditor = db.Column(db.String(100), nullable=True)
    ecoa = db.Column(db.String(50), nullable=True)
    account_number = db.Column(db.String(25), nullable=True)
    account_type = db.Column(db.String(25), nullable=False, default='other')
    push = db.Column(db.Boolean, nullable=True, default=False)
    last_collector = db.Column(db.String(100), nullable=True)
    collector_account = db.Column(db.String(100), nullable=True)
    last_debt_status = db.Column(db.String(100), nullable=True)
    bureaus = db.Column(db.String(100), nullable=True)
    days_delinquent = db.Column(db.String(20), nullable=True)
    balance_original = db.Column(db.String(20), nullable=True)
    payment_amount = db.Column(db.String(20), nullable=True)
    credit_limit = db.Column(db.String(20), nullable=True)
    graduation = db.Column(db.DateTime, nullable=True)

    def get_tasks_in_progress(self):
        return ScrapeTask.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return ScrapeTask.query.filter_by(name=name, user=self, complete=False).first()


class CreditPaymentPlan(db.Model):
    """ DB Model for storing various constants related to Credit Monitoring"""
    __tablename__ = "credit_payment_plan"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False) 

    enrolled_percent = db.Column(db.Float, nullable=False)
    monthly_bank_fee = db.Column(db.Float, nullable=False)
    minimum_fee = db.Column(db.Float, nullable=False)

    monitoring_fee_1signer = db.Column(db.Float, nullable=False) 
    monitoring_fee_2signer = db.Column(db.Float, nullable=False) 
    
