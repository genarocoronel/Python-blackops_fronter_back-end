import enum
from sqlalchemy.orm import backref
from app.main.model.user import User
from sqlalchemy import and_

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

class ProgramStatus(enum.Enum):
    READY =  'ready' # before contract is signed
    SIGNED = 'signed' # Signed and first payment pending
    DROPPED = 'dropped' # cancelled before 1st payment
    ACTIVE = 'active' # after first payment
    COMPLETED = 'completed' # completed all payments 
    HOLD = 'hold' # payment failed , program on hold
    CANCELLED = 'cancelled' # cancelled after 1st payment


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
    addresses = db.relationship("Address", backref='client')
    contact_numbers = db.relationship('ClientContactNumber')
    # account manager
    team_manager = db.relationship('User', backref='team_accounts', foreign_keys=[team_manager_id])
    account_manager = db.relationship('User', backref=backref('service_accounts',  lazy='dynamic'), foreign_keys=[account_manager_id])
    sales_rep = db.relationship('User', backref=backref('sales_accounts', lazy='dynamic'), foreign_keys=[sales_rep_id])
    opener = db.relationship('User', backref=backref('opened_accounts', lazy='dynamic'), foreign_keys=[opener_id])
    notification_pref = db.relationship('NotificationPreference', uselist=False, backref='client')
    
    # fields
    suffix = db.Column(db.String(25), nullable=True)
    first_name = db.Column(db.String(25), nullable=False)
    middle_initial = db.Column(db.CHAR, nullable=True)
    last_name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    language = db.Column(db.String(25), nullable=True)
    best_time = db.Column(db.String(5), nullable=True) # Best time to call
    best_time_pos = db.Column(db.String(6), nullable=True) # Before/After/At
    loc_time_zone = db.Column(db.String(3), nullable=True) # PST/EST/etc.
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
    # EPPS Account Id
    epps_account_id  = db.Column(db.String(100), nullable=True)
    # program status
    program_status = db.Column(db.String(24), default=ProgramStatus.READY.name) 
    
    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    @property
    def status(self):
        result = ''
        if self.disposition: 
            result = self.disposition.value
        return result

    @status.setter
    def status(self, value):
        cd = ClientDisposition.query.filter_by(value=value).first()
        if cd:
            self.disposition_id = cd.id
 
    @property
    def status_name(self):
        result = ''
        if self.disposition:
            result = self.disposition.name
        return result

    @status_name.setter
    def status_name(self, name):
        cd = ClientDisposition.query.filter_by(name=name).first()
        if cd:
            self.disposition_id = cd.id

    @property
    def total_debt(self):
        from app.main.model.credit_report_account import CreditReportAccount, CreditReportData
        result = 0
        keys = [self.id,] 
        if self.co_client:
            keys.append(self.co_client.id)
        
        debts = CreditReportData.query.outerjoin(CreditReportAccount)\
                                      .filter(and_(CreditReportAccount.client_id.in_(keys), CreditReportData.push==True)).all()
        for debt in debts:
            result = result + float(debt.balance_original)
        return result

    @property
    def enrolled_debts(self):
        if self.credit_report_account:
            return self.credit_report_account.records
        return []

    @property
    def combined_debts(self):
        if self.co_client:
            return self.enrolled_debts + self.co_client.enrolled_debts
        return self.enrolled_debts

    # 'Inserted' to 'New Lead' transition => When any action happens on a file 
    #  that is in an "Inserted" status
    def update(self):
        if self.status == 'Inserted':
            self.status = 'New Lead'
        db.session.commit()


class ClientIncome(db.Model):
    __tablename__ = "client_income_sources"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    income_id = db.Column(db.Integer, db.ForeignKey('income_sources.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref=backref('income_source_client_assoc', cascade="all, delete-orphan"))
    income_source = db.relationship('Income', backref=backref('client_income_source_assoc', cascade="all, delete-orphan"))


class ClientMonthlyExpense(db.Model):
    __tablename__ = "client_monthly_expenses"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('monthly_expenses.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref=backref('monthly_expense_client_assoc', cascade="all, delete-orphan"))
    monthly_expense = db.relationship('MonthlyExpense', backref=backref('client_monthly_expense_assoc', cascade="all, delete-orphan"))


class ClientEmployment(db.Model):
    __tablename__ = "client_employments"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    employment_id = db.Column(db.Integer, db.ForeignKey('employments.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref=backref('client_employment_assoc', cascade="all, delete-orphan"))
    employment = db.relationship('Employment', backref=backref('employment_client_assoc', cascade="all, delete-orphan"))


class ClientContactNumber(db.Model):
    __tablename__ = "client_contact_numbers"

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True)
    contact_number_id = db.Column(db.Integer, db.ForeignKey('contact_numbers.id'), primary_key=True)

    # relationships
    client = db.relationship('Client', backref=backref('contact_number_client_assoc', cascade="all, delete-orphan"))
    contact_number = db.relationship('ContactNumber', backref=backref('client_contact_number_assoc', cascade="all, delete-orphan"))


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

