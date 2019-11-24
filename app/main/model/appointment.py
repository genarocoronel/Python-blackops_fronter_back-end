from app.main import db


class Appointment(db.Model):
    """ Appointment Model for storing appointment details"""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, nullable=False)
    employee_id = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    summary = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.TEXT, nullable=True)
    reminder_types = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(64), nullable=False)
    public_id = db.Column(db.String(100), unique=True)
