import enum
from flask import current_app

from app.main import db


class CreditReportSignupStatus(enum.Enum):
    INITIATING_SIGNUP = 'initiating_signup'
    ACCOUNT_CREATED = 'account_created'
    ACCOUNT_VALIDATING = 'account_validating'
    ACCOUNT_VALIDATED = 'account_validated'
    FULL_MEMBER = 'full_member'


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
