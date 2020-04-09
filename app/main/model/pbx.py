import enum

from app.main.model.user import Department
from .. import db


class PBXNumber(db.Model):
    """ PBX Number Model for storing PBX details"""
    __tablename__ = "pbx_numbers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # relationships
    voice_communications = db.relationship('VoiceCommunication', back_populates='pbx_number')
    fax_communications = db.relationship('FaxCommunication', back_populates='pbx_number')

    number = db.Column(db.BigInteger, nullable=False, unique=True)
    department = db.Column(db.Enum(Department), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    updated_on = db.Column(db.DateTime, nullable=False)


class CommunicationType(enum.Enum):
    pass


class TextCommunicationType(CommunicationType):
    FAX = 'fax'


class VoiceCommunicationType(CommunicationType):
    RECORDING = 'recording'
    VOICEMAIL = 'voicemail'


class VoiceCommunication(db.Model):
    """ PBX Voice Communication Model for storing Recording / Voicemail details """
    __tablename__ = "voice_communications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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


class FaxCommunication(db.Model):
    """ PBX Fax Communication Model for storing Fax details """
    __tablename__ = "fax_communications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

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
    updated_on = db.Column(db.DateTime, nullable=False)
    is_viewed = db.Column(db.Boolean, nullable=False, default=False)
