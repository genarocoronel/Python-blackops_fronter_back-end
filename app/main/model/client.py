import enum

from .. import db


class ClientType(enum.Enum):
    lead = "lead"
    client = "client"

class EmploymentStatus(enum.Enum):
    EMPLOYED = 'employed'
    RETIRED = 'retired'
    STUDENT = 'student'
    UNEMPLOYED = 'unemployed'

class ClientDisposition(db.Model):
    __tablename__ = "client_dispositions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # relationships
    clients = db.relationship('Client', back_populates='disposition')

    # fields
    value = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)


class Client(db.Model):
    """ Client Model for storing client related details """
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.Enum(ClientType), nullable=False, default=ClientType.lead)

    # foreign keys
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    disposition_id = db.Column(db.Integer, db.ForeignKey('client_dispositions.id'))

    # relationships
    disposition = db.relationship('ClientDisposition', back_populates='clients')
    bank_account = db.relationship('BankAccount', uselist=False, backref='client')
    credit_report_account = db.relationship('CreditReportAccount', uselist=False, backref='client')
    co_client = db.relationship('Client', uselist=False, remote_side=[client_id])
    employments = db.relationship('ClientEmployment')
    income_sources = db.relationship('ClientIncome')
    monthly_expenses = db.relationship('ClientMonthlyExpense')

    # fields
    suffix = db.Column(db.String(25), nullable=True)
    first_name = db.Column(db.String(25), nullable=False)
    middle_initial = db.Column(db.CHAR, nullable=True)
    last_name = db.Column(db.String(25), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zip = db.Column(db.Integer, nullable=False)
    zip4 = db.Column(db.Integer, nullable=False)
    county = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(25), nullable=True)
    phone = db.Column(db.String(25), nullable=True)
    # date of birth
    dob  = db.Column(db.DateTime, nullable=True)
    # SSN ID, string format to store '000-00-0000' or '000000000'
    ssn = db.Column(db.String(11), nullable=True) 

    estimated_debt = db.Column(db.Integer, nullable=False)

    employment_status = db.Column(db.Enum(EmploymentStatus), nullable=True)


class ClientIncome(db.Model):
    __tablename__ = "client_income_sources"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    income_id = db.Column(db.Integer, db.ForeignKey('income_sources.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref='income_source_client_assoc')
    income_source = db.relationship('Income', backref='client_income_source_assoc')


class ClientMonthlyExpense(db.Model):
    __tablename__ = "client_monthly_expenses"

    candidate_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('monthly_expenses.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref='monthly_expense_client_assoc')
    monthly_expense = db.relationship('MonthlyExpense', backref='client_monthly_expense_assoc')


class ClientEmployment(db.Model):
    __tablename__ = "client_employments"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    employment_id = db.Column(db.Integer, db.ForeignKey('employments.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref='client_employment_assoc')
    employment = db.relationship('Employment', backref='employment_client_assoc')
