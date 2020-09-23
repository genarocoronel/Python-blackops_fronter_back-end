from app.main import db
from sqlalchemy.orm import backref
from datetime import datetime
import enum

class AppointmentStatus(enum.Enum):
    SCHEDULED = 'scheduled'
    MISSED = 'missed'
    INCOMPLETE = 'incomplete'
    COMPLETED = 'completed'

class AppointmentType(enum.Enum):
    SERVICE_CALL = 'service call'  # Auto service schedule 
    MANUAL = 'manual assigned'  # manual assigned
    SELF = 'self' # self created

class Appointment(db.Model):
    """ Appointment Model for storing appointment details"""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)

    # created date
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow)

    # client
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='appointments_client_id_fkey'))
    # service/sales agent
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id', name='appointments_agent_id_fkey'))

    # relationship
    client = db.relationship('Client', backref='appointments')
    agent = db.relationship('User', backref='appointments', foreign_keys=[agent_id])
    
    scheduled_at = db.Column(db.DateTime, nullable=False)
    loc_time_zone = db.Column(db.String(50), nullable=True)
    # summary/title 
    summary = db.Column(db.String(255), nullable=False)

    # appointment type
    type = db.Column(db.String(24), nullable=True, default=AppointmentType.MANUAL.name)

    # status (appointmentstatus)
    status = db.Column(db.String(64), nullable=False, default=AppointmentStatus.SCHEDULED.name)
    # reminder options
    # TODO change to relational object
    reminder_types = db.Column(db.String(64), nullable=True)

    # ON Service Schedule Complete
    def on_ss_complete(self):
        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.COMPLETED.name
            db.session.commit() 

    # ON Service Schedule InComplete
    def on_ss_incomplete(self):
        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.INCOMPLETE.name
            db.session.commit() 

class AppointmentNote(db.Model):
    """ db model for storing appointment notes"""
    __tablename__ = "appointment_notes" 
   
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', name='appointment_notes_author_id_fkey'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', name='appointment_notes_appointment_id_fkey'))
    # relationship
    author = db.relationship('User', backref='appointment_notes') 
    appointment = db.relationship('Appointment', backref=backref('notes', cascade="all, delete-orphan"))

    # note contents
    content = db.Column(db.String(1000), nullable=False) 
