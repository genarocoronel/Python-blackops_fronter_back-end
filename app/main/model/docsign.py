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

class SessionState(enum.Enum):
    PROGRESS = 'InProgress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    
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
    # relationships
    sessions = db.relationship('DocusignSession', back_populates='template')

# Session is created 
# when a document is send for signatures
class DocusignSession(db.Model):
    __tablename__ = "docusign_session"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    template_id = db.Column(db.Integer,  db.ForeignKey('docusign_template.id'), nullable=False) 
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    state = db.Column(db.Enum(SessionState), nullable=False, default=SessionState.PROGRESS) 
    # primary client id
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    cosign_required = db.Column(db.Boolean, default=False)

    # relationships
    signatures = db.relationship('DocusignSignature', back_populates='session')
    template   = db.relationship('DocusignTemplate', back_populates='sessions')

class DocusignSignature(db.Model):
    """
    Model for storing remote signature information
    """
    __tablename__ = "docusign_signature"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    envelope_id = db.Column(db.String(200), unique=True, nullable=False)
    status = db.Column(db.Enum(SignatureStatus), nullable=False, default=SignatureStatus.SENT)
    modified = db.Column(db.DateTime, default=datetime.utcnow)
    is_primary = db.Column(db.Boolean, default=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('docusign_session.id'), nullable=True)

    # relationships
    session = db.relationship('DocusignSession', back_populates='signatures')
