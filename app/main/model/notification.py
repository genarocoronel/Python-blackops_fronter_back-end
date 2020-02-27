import enum

from .. import db

class CallOptions(enum.Enum):
    home = "home"
    work = "work"
    mobile = "mobile" 

# Appointment reminder options
class ApptReminderOptions(enum.Enum):
    text = "text"
    email = "email"
    call = "call"
    none = "none"

# Document notification options
class DocNotificationOptions(enum.Enum):
    text = "text"
    email = "email"
    post = "post"
    fax = "fax"

# Payment Reminder options 
class PymtReminderOptions(enum.Enum):
    email = "email"
    call = "call"


class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # foreign key
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))

    service_call = db.Column(db.Enum(CallOptions), nullable=False, default=CallOptions.mobile)
    appt_reminder = db.Column(db.Enum(ApptReminderOptions), nullable=False, default=ApptReminderOptions.text)
    doc_notification = db.Column(db.Enum(DocNotificationOptions), nullable=False, default=DocNotificationOptions.text)
    payment_reminder = db.Column(db.Enum(PymtReminderOptions), nullable=False, default=PymtReminderOptions.email)
    

