from flask import current_app
from datetime import datetime
import enum

from app.main.model.client import ClientDisposition
from app.main import db

class DocusignSessionStatus(enum.Enum):
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

# Session is created 
# when a document is send for signatures
class DocusignSession(db.Model):
    __tablename__ = "docusign_session"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    template_id  = db.Column(db.Integer,  db.ForeignKey('docusign_template.id'), nullable=False) 
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow)

    envelope_id = db.Column(db.String(200), unique=True, nullable=False)
    status = db.Column(db.Enum(DocusignSessionStatus), default=DocusignSessionStatus.SENT)

    # primary client id
    contract_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id'), nullable=True)

    # relationships
    template   = db.relationship('DocusignTemplate', backref='sessions')
    contract   = db.relationship('DebtPaymentContract', backref='docusign_sessions')


# Model Helper function to pre-poulate the database tables related to docusign
def populate_docusign_client_dispositions():
    records = [{'value': 'Contract Sent', 'description': 'Contract is sent to client for signature'},
               {'value': 'Contract Opened', 'description': 'Contract Opened by the client'},
               {'value': 'Contract Signed', 'description': 'Client has finished signing the document'},
               {'value': 'Contract Completed', 'description': 'Client has completed signing the document'},
               {'value': 'Contract Declined', 'description': 'Contract was declined by the client'},
               {'value': 'Contract Voided', 'description': 'Contract was voided by the client'},
               {'value': 'Contract Deleted', 'description': 'Contract was deleted by the client'},]

    for record in records:
        cd = ClientDisposition(value=record['value'], description=record['description'])
        db.session.add(cd)
        db.session.flush()
    db.session.commit()

