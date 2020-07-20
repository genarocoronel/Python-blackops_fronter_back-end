import enum
from sqlalchemy.orm import backref
from app.main.model.user import User

from .. import db


class ClientType(enum.Enum):
    lead = "lead"
    client = "client"
    coclient = "coclient"


class EmploymentStatus(enum.Enum):
    EMPLOYED = 'employed'
    RETIRED = 'retired'
    STUDENT = 'student'
    UNEMPLOYED = 'unemployed'
    
    @staticmethod
    def frm_text(txt):
        if txt.lower() in 'employed':
            return EmploymentStatus.EMPLOYED
        elif txt.lower() in 'retired':
            return EmploymentStatus.RETIRED
        elif txt.lower() in 'student':
            return EmploymentStatus.STUDENT
        elif txt.lower() in 'unemployed':
            return EmploymentStatus.UNEMPLOYED


class ClientDispositionType(enum.Enum):
    MANUAL = 'manual'
    AUTO = 'auto'


class ClientDisposition(db.Model):
    __tablename__ = "client_dispositions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    select_type = db.Column(db.Enum(ClientDispositionType), nullable=False, default=ClientDispositionType.MANUAL)

    # relationships
    clients = db.relationship('Client', back_populates='disposition')

    # fields
    name = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)


class Client(db.Model):
    """ Client Model for storing client related details """
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    friendly_id = db.Column(db.String(24), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.Enum(ClientType), nullable=False, default=ClientType.lead)

    # foreign keys
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    disposition_id = db.Column(db.Integer, db.ForeignKey('client_dispositions.id'))
    account_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sales_rep_id = db.Column(db.Integer, db.ForeignKey('users.id', name='clientst_sales_rep_id_fkey'))
    opener_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    team_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # relationships
    disposition = db.relationship('ClientDisposition', back_populates='clients')
    bank_account = db.relationship('BankAccount', uselist=False, backref='client')
    credit_report_account = db.relationship('CreditReportAccount', uselist=False, backref='client')
    co_client = db.relationship('Client', uselist=False, remote_side=[client_id])
    employments = db.relationship('ClientEmployment')
    income_sources = db.relationship('ClientIncome')
    monthly_expenses = db.relationship('ClientMonthlyExpense')
    addresses = db.relationship("Address", backref="client")
    contact_numbers = db.relationship('ClientContactNumber')
    # account manager
    account_manager = db.relationship('User', backref='client_accounts', foreign_keys=[account_manager_id])
    team_manager = db.relationship('User', backref='team_accounts', foreign_keys=[team_manager_id])
    opener = db.relationship('User', backref='opened_accounts', foreign_keys=[opener_id])
    sales_rep = db.relationship('User', backref='sales_accounts', foreign_keys=[sales_rep_id])
    notification_pref = db.relationship('NotificationPreference', uselist=False, backref='client')
    
    # fields
    suffix = db.Column(db.String(25), nullable=True)
    first_name = db.Column(db.String(25), nullable=False)
    middle_initial = db.Column(db.CHAR, nullable=True)
    last_name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(25), nullable=True)
    # date of birth
    dob  = db.Column(db.DateTime, nullable=True)
    # SSN ID
    ssn = db.Column(db.String(9), nullable=True) 
    estimated_debt = db.Column(db.Integer, nullable=False)
    employment_status = db.Column(db.Enum(EmploymentStatus), nullable=True)
    # record modified date
    modified_date = db.Column(db.DateTime, nullable=True)
    # campaign name copied from candidate
    campaign_name = db.Column(db.String(100), nullable=True)
    # lead source
    lead_source = db.Column(db.String(100), nullable=True)
    # date on which application is processed
    application_date = db.Column(db.DateTime, nullable=True)   

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)


class ClientIncome(db.Model):
    __tablename__ = "client_income_sources"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    income_id = db.Column(db.Integer, db.ForeignKey('income_sources.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref='income_source_client_assoc')
    income_source = db.relationship('Income', backref='client_income_source_assoc')


class ClientMonthlyExpense(db.Model):
    __tablename__ = "client_monthly_expenses"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
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


class ClientContactNumber(db.Model):
    __tablename__ = "client_contact_numbers"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    contact_number_id = db.Column(db.Integer, db.ForeignKey('contact_numbers.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref='contact_number_client_assoc')
    contact_number = db.relationship('ContactNumber', backref='client_contact_number_assoc')


class ClientCheckList(db.Model):
    __tablename__ = "client_checklist"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey('checklist.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref='checklist')
    checklist = db.relationship('CheckList', backref='client_checklist')


class ClientVoiceCommunication(db.Model):
    __tablename__ = "client_voice_communications"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    voice_communication_id = db.Column(db.Integer, db.ForeignKey('voice_communications.id'), primary_key=True)

    client = db.relationship('Client', backref='voice_communication_client_assoc')
    voice_communication = db.relationship('VoiceCommunication', backref='client_voice_communication_assoc')


class ClientFaxCommunication(db.Model):
    __tablename__ = "client_fax_communications"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    fax_communication_id = db.Column(db.Integer, db.ForeignKey('fax_communications.id'), primary_key=True)

    client = db.relationship('Client', backref='fax_communication_client_assoc')
    fax_communication = db.relationship('FaxCommunication', backref='client_fax_communication_assoc')

# client campaign association
class ClientCampaign(db.Model):
    __tablename__ = "client_campaigns"

    # foreign keys
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), primary_key=True)

    # relationships
    client = db.relationship("Client", backref=backref('campaign_assoc', cascade="all, delete-orphan")) 
    campaign = db.relationship("Campaign", backref=backref('client_assoc', cascade="all, delete-orphan", lazy='dynamic')) 

