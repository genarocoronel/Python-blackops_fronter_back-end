import enum

from .. import db

class CallOptions(enum.Enum):
    HOME = "home"
    WORK = "work"
    MOBILE = "mobile" 

# Appointment reminder options
class ApptReminderOptions(enum.Enum):
    TEXT = "text"
    EMAIL = "email"
    CALL = "call"
    NONE = "none"

# Document notification options
class DocNotificationOptions(enum.Enum):
    TEXT = "text"
    EMAIL = "email"
    POST = "post"
    FAX = "fax"

# Payment Reminder options 
class PymtReminderOptions(enum.Enum):
    EMAIL = "email"
    CALL = "call"
    NONE = "none"

class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # foreign key
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))

    service_call = db.Column(db.Enum(CallOptions), nullable=False, default=CallOptions.MOBILE)
    appt_reminder = db.Column(db.Enum(ApptReminderOptions), nullable=False, default=ApptReminderOptions.TEXT)
    doc_notification = db.Column(db.Enum(DocNotificationOptions), nullable=False, default=DocNotificationOptions.TEXT)
    payment_reminder = db.Column(db.Enum(PymtReminderOptions), nullable=False, default=PymtReminderOptions.EMAIL)
    

