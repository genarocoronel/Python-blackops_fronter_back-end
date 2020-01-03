import enum
from app.main import db
from datetime import datetime
from sqlalchemy import func


class DebtEftStatus(enum.Enum):
    Scheduled = 'Scheduled'  # EFT Scheduled , Not forwarded to EPPS
    Processed = 'Processed'  # Processed, Sent to EPPS
    Settled   = 'Settled'    # EFT Transfer completed
    Failed    = 'Failed'     # EFT Payment failed

class DebtPaymentSchedule(db.Model):
    """ DB model for storing debt payment schedule and payment status."""   
    __tablename__ = "debt_payment_schedule"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # relationship
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='fk_client'))
    due_date = db.Column(db.DateTime, nullable=False)
    amount  = db.Column(db.Float, nullable=False)
    bank_fee = db.Column(db.Float, nullable=True)
    status  = db.Column(db.Enum(DebtEftStatus), nullable=False, default=DebtEftStatus.Scheduled)

    # single EPPS transaction allowed, so One-to-One
    transactions = db.relationship("DebtPaymentTransaction", backref="debt_payment_schedule") 
    client = db.relationship("Client", backref="debt_payment_schedule")

class DebtPaymentTransaction(db.Model):
    """ DB model for storing transaction details of debt payment record."""
    __tablename__ = "debt_payment_transaction"
  
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # EFT transaction
    trans_id = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(200), nullable=False)
    # status message
    message = db.Column(db.Text,  nullable=True)
    provider = db.Column(db.String(40), nullable=False, default="EPPS")

    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # payment schedule foriegn key 
    payment_id = db.Column(db.Integer, db.ForeignKey(DebtPaymentSchedule.id))
