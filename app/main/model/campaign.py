import enum
from flask import current_app

from app.main import db

class MarketingModel(enum.Enum):
    PI = 'PI'
    PURL = 'PURL'
    CUSTOM = 'Custom'

class MailType(enum.Enum): 
    BPLUSWSNAP = 'B+WSNAP'
    PINKSNAP = 'PinkSnap'
    GREENSNAP = 'GreenSnap'
    BLUESNAP = 'BlueSnap'
    ENVELOPE = 'Envelope'
    CUSTOM = 'Custom'
    TEST = 'Test'
    TESTPINKSNAP = 'TestPinkSnap'
    TESTGREENSNAP = 'TestGreenSnap'

class PinnaclePhoneNumber(db.Model):
    """ Campaign Pinnacle Phone Model """
    __tablename__ = 'pinnacle_phone_numbers'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    number = db.Column(db.String(20), nullable=False, unique=True)

class Campaign(db.Model):
    """ Campaign Model """
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # relationships
    candidates = db.relationship('Candidate', back_populates='campaign', lazy='dynamic')
    # Pinnacle number
    pinnacle_phone_num_id = db.Column(db.Integer, db.ForeignKey('pinnacle_phone_numbers.id', name='campaigns_pinnacle_phone_num_id_fkey'))
    pinnacle_phone_num = db.relationship('PinnaclePhoneNumber', backref='campaigns')

    # fields
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(25), nullable=False)
    job_number = db.Column(db.String(75), unique=True, nullable=False)
    mailing_date = db.Column(db.String(10), nullable=False)
    offer_expire_date = db.Column(db.String(10), nullable=False)
    mailer_file = db.Column(db.String(100), unique=True, nullable=True)

    # Marketing type 
    marketing_model = db.Column(db.String(40), default=MarketingModel.PI.value)
    # type of mail
    mail_type =  db.Column(db.String(40), default=MailType.BPLUSWSNAP.value)
    # Number of mail pieces
    num_mail_pieces = db.Column(db.Integer, default=0)
    cost_per_piece =  db.Column(db.Float, default=0.16)
    # estimated debt range
    est_debt_range = db.Column(db.JSON, default={'min': 0, 'max': 0})


    def launch_task(self, name, *args, **kwargs):
        rq_job = current_app.queue.enqueue('app.main.tasks.campaign.' + name, self.id, *args, **kwargs)
        return rq_job.get_id()
