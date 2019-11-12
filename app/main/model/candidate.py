import enum

from flask import current_app

from app.main.model.task import ImportTask
from .. import db


class CandidateStatus(enum.Enum):
    IMPORTED = 'imported'  # Candidate has been imported but not submitted to Redstone for contact
    CAMPAIGNED = 'campaigned'  # Submitted to Redstone for contact
    WORKING = 'working'  # Being worked by opener rep
    SUBMITTED = 'submitted'


class CandidateDisposition(db.Model):
    __tablename__ = "candidate_dispositions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # relationships
    candidates = db.relationship('Candidate', back_populates='disposition')

    # fields
    value = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    disposition_id = db.Column(db.Integer, db.ForeignKey('candidate_dispositions.id'))
    import_id = db.Column(db.Integer, db.ForeignKey('candidate_imports.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))

    # relationships
    import_record = db.relationship('CandidateImport', back_populates='candidates')
    credit_report_account = db.relationship('CreditReportAccount', uselist=False, backref='candidate')
    disposition = db.relationship('CandidateDisposition', back_populates='candidates')
    campaign = db.relationship('Campaign', back_populates='candidates')

    # fields
    first_name = db.Column(db.String(25), nullable=False)
    middle_initial = db.Column(db.CHAR, nullable=True)
    last_name = db.Column(db.String(25), nullable=False)
    suffix = db.Column(db.String(25), nullable=True)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    _zip = db.Column('zip', db.String(5), nullable=False)
    zip4 = db.Column(db.String(4), nullable=False)
    status = db.Column(db.Enum(CandidateStatus), nullable=True, default=CandidateStatus.IMPORTED)
    estimated_debt = db.Column(db.Integer, nullable=False)

    prequal_number = db.Column(db.String(12), unique=True, nullable=True)

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

    county = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    language = db.Column(db.String(25), nullable=True)
    phone = db.Column(db.String(25), nullable=True)

    @property
    def zip(self):
        return f'{self._zip}-{self.zip4}'

    @property
    def zip5(self):
        return self._zip

    @zip.setter
    def zip(self, zip):
        self._zip = zip.zfill(5)


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

    # relationships
    candidates = db.relationship('Candidate', back_populates='import_record', lazy='dynamic')
    tasks = db.relationship('ImportTask', backref='candidate_import', lazy='dynamic')

    # fields
    file = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(CandidateImportStatus), nullable=False, default=CandidateImportStatus.CREATED)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.main.tasks.' + name, self.id, *args, **kwargs)
        task = ImportTask(id=rq_job.get_id(), name=name, description=description, candidate_import=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return ImportTask.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return ImportTask.query.filter_by(name=name, user=self, complete=False).first()
