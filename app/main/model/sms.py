from .. import db


class SMSMessage(db.Model):
    """ SMS Model """
    __tablename__ = "sms_messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_provider_id = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.TEXT, nullable=False)
    phone_target = db.Column(db.String(25), nullable=False)
    status = db.Column(db.String(25), nullable=False)