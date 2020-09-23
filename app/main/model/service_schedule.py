import enum
from .. import db
from sqlalchemy.orm import backref


class ServiceScheduleStatus(enum.Enum):
    PENDING = 'pending'
    COMPLETE = 'complete'
    INCOMPLETE = 'incomplete'
    RESCHEDULED = 'rescheduled'

    @classmethod
    def is_valid_status(cls, status):
        statuses = set(item.value for item in cls)
        return status in statuses

class ServiceScheduleType(enum.Enum):
    INTRO_CALL = 'Introduction Call'
    CALL = 'Call' 
    TEXT = 'Text'
    CREDIT_PULL = 'Credit Pull'

class ServiceSchedule(db.Model):
    """ Represents a Service Schedule """
    __tablename__ = "service_schedule"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    schedule_item = db.Column(db.Integer, nullable=False)
    inserted_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)
    updated_by_username = db.Column(db.String(50))

    type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(25), default="pending")
    scheduled_for = db.Column(db.DateTime, nullable=True)
    tot_reschedule = db.Column(db.Integer, default=0)

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='fk_svc_schedule_client_id'), nullable=True)
    client = db.relationship('Client', backref=backref('service_schedule', cascade="all, delete-orphan"))

    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', name='fk_svc_schedule_appointment_id'), nullable=True)
    appointment = db.relationship('Appointment', backref='service_schedule', uselist=False)
