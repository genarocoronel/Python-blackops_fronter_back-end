import enum
from .. import db
from sqlalchemy.orm import backref

class BankAccountType(enum.Enum):
    checking = "checking"
    savings = "savings"

class StatusCategory(enum.Enum):
    passed = "passed"
    failed = "failed"

class BankAccount(db.Model):
    """ Client Bank Account Model """
    __tablename__ = "bank_accounts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    bav_status_id = db.Column(db.Integer, db.ForeignKey('bank_account_validation_status.id'), nullable=True)
    # relationships
    bav_status = db.relationship("BankAccountValidationStatus", backref="bank_accounts")

    # fields
    bank_name = db.Column(db.String(125), nullable=False)
    account_number = db.Column(db.String(100), nullable=False)
    routing_number = db.Column(db.String(9), nullable=False)
    valid = db.Column(db.Boolean, nullable=False)
    type = db.Column(db.Enum(BankAccountType), nullable=True, default=BankAccountType.checking)
    # bank details, optional 
    # if account owner details are differant than the lead details
    owner_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(30), nullable=True)
    state = db.Column(db.String(2), nullable=True)
    zip = db.Column(db.String(10), nullable=True)
    ssn = db.Column(db.String(9), nullable=True)

class BankAccountValidationStatus(db.Model):
    """ Bank Account Validation Status types"""
    __tablename__ = "bank_account_validation_status"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.Enum(StatusCategory), default=StatusCategory.failed)
    code = db.Column(db.String(10), nullable=False, unique=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)


class BankAccountValidationHistory(db.Model):
    """ Bank Account Validation History"""
    __tablename__ = "bank_account_validation_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    bav_status_id = db.Column(db.Integer, db.ForeignKey('bank_account_validation_status.id'), nullable=True)
    # relationships
    bav_status = db.relationship("BankAccountValidationStatus", backref=backref('bav_history', cascade="all, delete-orphan"))
    client = db.relationship("Client", backref=backref('bav_history', cascade="all, delete-orphan"))

    account_number = db.Column(db.String(100), nullable=False)
    routing_number = db.Column(db.String(9), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False) 
    
    # whether overriden or not
    overuled = db.Column(db.Boolean, default=False) 
    overuled_by = db.Column(db.Integer, db.ForeignKey('users.id', name='bank_account_validation_history_overruled_by_fkey'))

    overruler = db.relationship("User", backref="overruled_history")
   
