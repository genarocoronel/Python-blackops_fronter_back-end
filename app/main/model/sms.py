from .. import db

class SMSConvo(db.Model):
    """ Represents a SMS Client Conversation """
    __tablename__ = "sms_convos"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)
    
    # relationships
    sms_messages = db.relationship('SMSMessage', backref='sms_convo')
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='fk_client'))
    
    
class SMSMessage(db.Model):
    """ Represents a CRM SMS message """
    __tablename__ = 'sms_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)

    from_phone = db.Column(db.String(20)) 
    to_phone = db.Column(db.String(20))
    network_time = db.Column(db.String(25))
    direction = db.Column(db.String(20))
    segment_count = db.Column(db.Integer)
    body_text = db.Column(db.String(918))
    provider_message_id = db.Column(db.String(100))
    provider_name = db.Column(db.String(25))
    is_viewed = db.Column(db.Boolean, default=False)

    # Relationships
    sms_convo_id = db.Column(db.Integer, db.ForeignKey('sms_convos.id', name='fk_sms_convos_id'))
    sms_media_files = db.relationship('SMSMediaFile', backref='sms_message')


class SMSMediaFile(db.Model):
    """ Represents a (MMS) media file for a SMS message """
    __tablename__ = 'sms_media_files'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)

    file_uri = db.Column(db.String(500))

    # relationships
    sms_message_id = db.Column(db.Integer, db.ForeignKey('sms_messages.id'), name='fk_sms_message')


class SMSBandwidth(db.Model):
    """ Represents a Bandwidth SMS message """
    __tablename__ = 'sms_bandwidth'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime)

    is_imported = db.Column(db.Boolean, default=False)
    time = db.Column(db.String(25))
    type = db.Column(db.String(50))
    to = db.Column(db.String(20))
    description = db.Column(db.String(25))
    message_id = db.Column(db.String(100))
    message_owner = db.Column(db.String(20))
    message_application_id = db.Column(db.String(100))
    message_time = db.Column(db.String(25))
    message_segment_count = db.Column(db.Integer)
    message_direction = db.Column(db.String(20))
    message_to = db.Column(db.String(100))
    message_from = db.Column(db.String(20))
    message_text = db.Column(db.String(918))
    message_media = db.Column(db.String)
    