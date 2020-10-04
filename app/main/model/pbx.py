import enum

from app.main.model.user import Department
from .. import db


class PBXSystem(db.Model):
    """ PBX System Model for storing PBX system details """
    __tablename__ = "pbx_systems"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)

    # relationships
    pbx_numbers = db.relationship('PBXNumber', back_populates='pbx_system')

    name = db.Column(db.String, unique=True, nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=False)


class PBXNumber(db.Model):
    """ PBX Number Model for storing PBX details"""
    __tablename__ = "pbx_numbers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    pbx_system_id = db.Column(db.Integer, db.ForeignKey('pbx_systems.id'))

    # relationships
    voice_communications = db.relationship('VoiceCommunication', back_populates='pbx_number')
    fax_communications = db.relationship('FaxCommunication', back_populates='pbx_number')
    pbx_system = db.relationship('PBXSystem', back_populates='pbx_numbers')

    number = db.Column(db.BigInteger, nullable=False, unique=True)
    department = db.Column(db.Enum(Department), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=False)


class CommunicationType(enum.Enum):
    pass


class TextCommunicationType(CommunicationType):
    SMS = 'sms'
    FAX = 'fax'


class VoiceCommunicationType(CommunicationType):
    RECORDING   = 'recording'
    VOICEMAIL   = 'voicemail'
    MISSED_CALL = 'missed_call'


class VoiceCommunication(db.Model):
    """ PBX Voice Communication Model for storing Recording / Voicemail details """
    __tablename__ = "voice_communications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    pbx_number_id = db.Column(db.Integer, db.ForeignKey('pbx_numbers.id'))

    # relationships
    pbx_number = db.relationship('PBXNumber', back_populates='voice_communications')

    type = db.Column(db.Enum(VoiceCommunicationType), nullable=False)
    source_number = db.Column(db.BigInteger, nullable=False)
    destination_number = db.Column(db.BigInteger, nullable=True)
    outside_number = db.Column(db.BigInteger, nullable=True)
    receive_date = db.Column(db.DateTime, nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    provider_name = db.Column(db.String(100), nullable=False)
    provider_record_id = db.Column(db.String(100), nullable=True, unique=True)
    file_bucket_name = db.Column(db.String(50), nullable=False)
    file_bucket_key = db.Column(db.String(1024), nullable=False, unique=True)
    updated_on = db.Column(db.DateTime, nullable=False)
    is_viewed = db.Column(db.Boolean, nullable=False, default=False)


class PBXSystemVoiceCommunication(db.Model):
    """ PBX System to Voice Communication mapping Model """
    __tablename__ = "pbx_system_voice_communications"

    pbx_system_id = db.Column(db.Integer, db.ForeignKey('pbx_systems.id'), primary_key=True)
    voice_communication_id = db.Column(db.Integer, db.ForeignKey('voice_communications.id'), primary_key=True)

    # relationship
    pbx_system = db.relationship('PBXSystem', backref='pbx_system_voice_communication_assoc')
    voice_communication = db.relationship('VoiceCommunication', backref='voice_communication_pbx_system_assoc')


class FaxCommunication(db.Model):
    """ PBX Fax Communication Model for storing Fax details """
    __tablename__ = "fax_communications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    pbx_number_id = db.Column(db.Integer, db.ForeignKey('pbx_numbers.id'))

    # relationships
    pbx_number = db.relationship('PBXNumber', back_populates='fax_communications')

    source_number = db.Column(db.BigInteger, nullable=False)
    destination_number = db.Column(db.BigInteger, nullable=False)
    outside_number = db.Column(db.BigInteger, nullable=True)
    receive_date = db.Column(db.DateTime, nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    provider_name = db.Column(db.String(25), nullable=False)
    file_bucket_name = db.Column(db.String(50), nullable=False)
    file_bucket_key = db.Column(db.String(1024), nullable=False, unique=True)
    is_viewed = db.Column(db.Boolean, nullable=False, default=False)


class PBXSystemFaxCommunication(db.Model):
    """ PBX System to Fax Communication mapping Model """
    __tablename__ = "pbx_system_fax_communications"

    pbx_system_id = db.Column(db.Integer, db.ForeignKey('pbx_systems.id'), primary_key=True)
    fax_communication_id = db.Column(db.Integer, db.ForeignKey('fax_communications.id'), primary_key=True)

    # relationship
    pbx_system = db.relationship('PBXSystem', backref='pbx_system_fax_communication_assoc')
    fax_communication = db.relationship('FaxCommunication', backref='fax_communication_pbx_system_assoc')


class CallEventType(enum.Enum):
    INITIATED           = 'call_initiated'
    GOING_TO_VOICEMAIL  = 'going_to_voicemail'
    MISSED              = 'missed'
    MISSED_VOICEMAIL    = 'missed_voicemail'


class VoiceCallEvent(db.Model):
    """ PBX voice call event """
    __tablename__ = "voice_call_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)
    receive_date = db.Column(db.DateTime, nullable=True)

    pbx_id = db.Column(db.String, unique=False, nullable=False)
    pbx_call_id = db.Column(db.String, unique=True, nullable=False)
    caller_number = db.Column(db.BigInteger, unique=False, nullable=False)
    dialed_number = db.Column(db.BigInteger, unique=False, nullable=False)
    status = db.Column(db.Enum(CallEventType), unique=False, nullable=False)
    is_viewed = db.Column(db.Boolean, nullable=False, default=False)
