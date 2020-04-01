import enum
from .. import db


class ServiceScheduleStatus(enum.Enum):
    PENDING = 'pending'
    COMPLETE = 'complete'
    INCOMPLETE = 'incomplete'
    RESCHEDULED = 'rescheduled'

    @classmethod
    def is_valid_status(cls, status):
        statuses = set(item.value for item in cls)
        return status in statuses


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