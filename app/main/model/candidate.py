import enum

from flask import current_app

from app.main.model.client import EmploymentStatus
from app.main.model.task import ImportTask
from .. import db


class CandidateStatus(enum.Enum):
    IMPORTED = 'imported'  # Candidate has been imported but not submitted to Redstone for contact
    CAMPAIGNED = 'campaigned'  # Submitted to Redstone for contact
    WORKING = 'working'  # Being worked by opener rep
    SUBMITTED = 'submitted'
  
    @staticmethod
    def frm_text(txt):
        if txt.lower() in 'imported':
            return CandidateStatus.IMPORTED
        elif txt.lower() in 'campaigned':
            return CandidateStatus.CAMPAIGNED
        elif txt.lower() in 'working':
            return CandidateStatus.WORKING
        elif txt.lower() in 'submitted':
            return CandidateStatus.SUBMITTED
        else:
            return None


class CandidateDispositionType(enum.Enum):
    MANUAL = 'manual'
    AUTO = 'auto'


class CandidateDisposition(db.Model):
    __tablename__ = "candidate_dispositions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    select_type = db.Column(db.Enum(CandidateDispositionType), nullable=False, default=CandidateDispositionType.MANUAL)

    # relationships
    candidates = db.relationship('Candidate', back_populates='disposition')

    # fields
    name = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    prequal_number = db.Column(db.String(12), unique=True, nullable=True)
    status = db.Column(db.Enum(CandidateStatus), nullable=True, default=CandidateStatus.IMPORTED)

    # foreign keys
    disposition_id = db.Column(db.Integer, db.ForeignKey('candidate_dispositions.id'))
    import_id = db.Column(db.Integer, db.ForeignKey('candidate_imports.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))

    # relationships
    import_record = db.relationship('CandidateImport', back_populates='candidates')
    credit_report_account = db.relationship('CreditReportAccount', uselist=False, backref='candidate')
    disposition = db.relationship('CandidateDisposition', back_populates='candidates')
    campaign = db.relationship('Campaign', back_populates='candidates')
    employments = db.relationship('CandidateEmployment')
    contact_numbers = db.relationship('CandidateContactNumber')
    income_sources = db.relationship('CandidateIncome')
    monthly_expenses = db.relationship('CandidateMonthlyExpense')
    addresses = db.relationship("Address", backref="candidate")

    # fields
    suffix = db.Column(db.String(25), nullable=True)
    first_name = db.Column(db.String(25), nullable=False)
    middle_initial = db.Column(db.CHAR, nullable=True)
    last_name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    language = db.Column(db.String(25), nullable=True)
    employment_status = db.Column(db.Enum(EmploymentStatus), nullable=True)
    dob = db.Column(db.DateTime, nullable=True)
    best_time = db.Column(db.String(5), nullable=True) # Best time to call
    estimated_debt = db.Column(db.Integer, nullable=False)
    loc_time_zone = db.Column(db.String(3), nullable=True) # PST/EST/etc.
    _ssn = db.Column('ssn', db.String(10), nullable=True)

    # mailer fields
    debt3 = db.Column(db.Integer, nullable=False)  # Debt3 = 3% of revolving debt so =DEBT*3% assuming Debt is column L
    debt15 = db.Column(db.Integer, nullable=False)  # DEBT*1.5% = (L9+(L9*0.06))/60 assuming that L is the column that has the persons revolving debt
    debt2 = db.Column(db.Integer, nullable=False)  # DEBT2 Subtract $5000 from Revolving Debt amount column
    debt215 = db.Column(db.Integer, nullable=False)  # DEBT2*1.5% = (O9+(O9*0.06))/60 assuming Column O is revolving debt -5000
    debt3_2 = db.Column(db.Integer, nullable=False)  # DEBT3_2 = Add $5000 to revolving Debt column number
    checkamt = db.Column(db.Integer, nullable=False)  # Checkamt Equal to revolving debt + $5000  or Debt3_2 column
    spellamt = db.Column(db.String(100), nullable=False)  # SpellAmt Goes to this site to make it convert as my computer wont do it                         https://support.office.com/en-us/article/convert-numbers-into-words-a0d166fb-e1ea-4090-95c8-69442cd55d98
    debt315 = db.Column(db.Integer, nullable=False)  # TOT_INT DEBT3*1.5% =(Q9+(Q9*0.06))/60 assuming Column Q is the add $5000 to revolving debt column
    year_interest = db.Column(db.Integer, nullable=False)  # INT_YR = L9*18.99% assuming that L is revolving Debt column
    total_interest = db.Column(db.Integer, nullable=False)  # TOT_INT = (U9*22)-L3 assuming S=interest per year and L is total revolving debt column
    sav215 = db.Column(db.Integer, nullable=False)  # SAV215 = (((O9*0.03)-P9)*12)-4 Assuming that O is the Debt 2 column and P is the Debt215 column
    sav15 = db.Column(db.Integer, nullable=False)  # SAV15 = (M9*12)-(N9*12) assuming that column M is Debt3 and Column N is Debt15
    sav315 = db.Column(db.Integer, nullable=False)  # Sav315 = (((Q9*0.03)-R9)*12)+4 assuming that Q is the Debt3 column and R is the Debt 315 column

    @property
    def ssn4(self):
        if self._ssn:
            if len(self._ssn) > 5:
                return self._ssn[-4:]            
        return ''


class CandidateContactNumber(db.Model):
    __tablename__ = "candidate_contact_numbers"

    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), primary_key=True)
    contact_number_id = db.Column(db.Integer, db.ForeignKey('contact_numbers.id'), primary_key=True)

    # relationships
    candidate = db.relationship('Candidate', backref='contact_number_candidate_assoc')
    contact_number = db.relationship('ContactNumber', backref='candidate_contact_number_assoc')


class CandidateIncome(db.Model):
    __tablename__ = "candidate_income_sources"

    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), primary_key=True)
    income_id = db.Column(db.Integer, db.ForeignKey('income_sources.id'), primary_key=True)

    # relationships
    candidate = db.relationship('Candidate', backref='income_source_candidate_assoc')
    income_source = db.relationship('Income', backref='candidate_income_source_assoc')


class CandidateMonthlyExpense(db.Model):
    __tablename__ = "candidate_monthly_expenses"

    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('monthly_expenses.id'), primary_key=True)

    # relationships
    candidate = db.relationship('Candidate', backref='monthly_expense_candidate_assoc')
    monthly_expense = db.relationship('MonthlyExpense', backref='candidate_monthly_expense_assoc')


class CandidateImportStatus(enum.Enum):
    CREATED = "created"  # waiting on task to be enqueued
    RECEIVED = "received"  # task has been enqueued
    RUNNING = "running"  # task is being executed and has not finished
    FINISHED = "finished"  # task completed successfully
    ERROR = "error"  # task finished with error


class CandidateImport(db.Model):
    """ Candidate Import Model for importing candidates from file upload """
    __tablename__ = "candidate_imports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)

    # relationships
    candidates = db.relationship('Candidate', back_populates='import_record', lazy='dynamic')
    tasks = db.relationship('ImportTask', backref='candidate_import', lazy='dynamic')

    # fields
    file = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(CandidateImportStatus), nullable=False, default=CandidateImportStatus.CREATED)

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.queue.enqueue('app.main.tasks.' + name, self.id, *args, **kwargs)
        task = ImportTask(id=rq_job.get_id(), name=name, description=description, candidate_import=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return ImportTask.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return ImportTask.query.filter_by(name=name, user=self, complete=False).first()


class CandidateEmployment(db.Model):
    __tablename__ = "candidate_employments"

    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), primary_key=True)
    employment_id = db.Column(db.Integer, db.ForeignKey('employments.id'), primary_key=True)

    # relationships
    candidate = db.relationship('Candidate', backref='candidate_employment_assoc')
    employment = db.relationship('Employment', backref='employment_candidate_assoc')


class CandidateVoiceCommunication(db.Model):
    __tablename__ = "candidate_voice_communications"

    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), primary_key=True)
    voice_communication_id = db.Column(db.Integer, db.ForeignKey('voice_communications.id'), primary_key=True)

    candidate = db.relationship('Candidate', backref='voice_communication_candidate_assoc')
    voice_communication = db.relationship('VoiceCommunication', backref='candidate_voice_communication_assoc')


class CandidateFaxCommunication(db.Model):
    __tablename__ = "candidate_fax_communications"

    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), primary_key=True)
    fax_communication_id = db.Column(db.Integer, db.ForeignKey('fax_communications.id'), primary_key=True)

    candidate = db.relationship('Candidate', backref='fax_communication_candidate_assoc')
    fax_communication = db.relationship('FaxCommunication', backref='candidate_fax_communication_assoc')
