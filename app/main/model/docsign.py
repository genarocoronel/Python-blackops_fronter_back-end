from flask import current_app
from datetime import datetime
import enum

from app.main import db

class SignatureStatus(enum.Enum):
    SENT = 'Sent'
    CREATED = 'Created'
    DELIVERED = 'Delivered'
    COMPLETED = 'Completed'
    DECLINED = 'Declined'
    SIGNED = 'Signed'
    VOIDED = 'Voided'
    

class DocusignTemplate(db.Model):
    """
    Model for storing Docusign template information
    """
    __tablename__ = "docusign_template"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Name of the template in Docusign
    name = db.Column(db.String(200), nullable=False)
    # Docusign template id
    ds_key = db.Column(db.String(200), unique=True, nullable=False)

class DocusignSignature(db.Model):
    """
    Model for storing remote signature information
    """
    __tablename__ = "docusign_signature"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    envelope_id = db.Column(db.String(200), unique=True, nullable=False)
    status = db.Column(db.Enum(SignatureStatus), nullable=False, default=SignatureStatus.SENT)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    template_id = db.Column(db.Integer,  db.ForeignKey('docusign_template.id'), nullable=False)
