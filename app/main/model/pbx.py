import enum

from .. import db


class PBXNumber(db.Model):
    """ PBX Number Model for storing PBX details"""
    __tablename__ = "pbx_numbers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    number = db.Column(db.String, nullable=False, unique=True)
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    updated_on = db.Column(db.DateTime, nullable=False)


class VoiceCommunicationType(enum.Enum):
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
    outside_number = db.Column(db.String, nullable=False, unique=False)
    updated_on = db.Column(db.DateTime, nullable=False)
