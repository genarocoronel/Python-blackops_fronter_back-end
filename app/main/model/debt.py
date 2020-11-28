from .. import db
from sqlalchemy.orm import backref
import enum
from datetime import datetime

class DebtDisputeStatus(enum.Enum):
    # P1 Send
    P1_SEND = 'Initial Dispute Send'
    SOLD_PACKAGE_SEND = 'Sold Package Send'
    NOIR_SEND = 'NOIR Send'
    NOIR2_SEND = 'NOIR2 Send'  
    NOIR_FDCPA_SEND = 'NOIR FDCPA Send'
    NOIR_FDCPA_WAIT = 'NOIR FDCPA Wait'
    P2_SEND = 'P2 Send' # P2 fax/mail to colector & non_response_sent_ack to client
    FULLY_DISPUTED_NON_RESPONSE_EXPIRED = 'Fully Disputed: Non Response Expired'
    FULLY_DISPUTED_NOIR_EXPIRED = 'Fully Disputed: Noir Expired'  # Send fully_disputed_notice template to client 
    FULLY_DISPUTED_EXPIRED = 'Fully Disputed: Expired' # Send fully_disputed_notice template to client
    # currently not used in SM 
    FULLY_DISPUTED_NOIR2_EXPIRED = 'Fully Disputed: Noir2 Expired'  # Send fully_disputed_notice template to client 
    FULLY_DISPUTED_FDCPA_EXPIRED = 'Fully Disputed: Noir FDCPA Expired'  # Send fully_disputed_notice template to client 


class DebtDispute(db.Model):
    """ Represents a Debt Dispute details """
    __tablename__ = "debt_disputes"

    # primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # client    
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='debt_disputes_client_id_fkey'), nullable=False)
    client = db.relationship('Client', backref=backref('debt_disputes', lazy='dynamic'))
    # debt
    debt_id = db.Column(db.Integer, db.ForeignKey('credit_report_data.id', name='debt_disputes_debt_id_fkey'), nullable=False)
    debt = db.relationship('CreditReportData', backref='debt_disputes')
    # collector
    collector_id = db.Column(db.Integer, db.ForeignKey('debt_collectors.id', name='debt_disputes_collector_id_fkey'), nullable=False)
    collector = db.relationship('DebtCollector', backref='debt_disputes')

    # p1 send date
    p1_date = db.Column(db.DateTime, nullable=True)
    # p2 send date
    p2_date = db.Column(db.DateTime, nullable=True)
    # NOIR send date
    noir_date = db.Column(db.DateTime, nullable=True)
    # Fully Disputed Noir Expired
    fd_noir_expired_date = db.Column(db.DateTime, nullable=True)
    # NOIR2 send date
    noir2_date = db.Column(db.DateTime, nullable=True)
    # noir fdcpa date
    noir_fdcpa_date = db.Column(db.DateTime, nullable=True) 
    fd_non_response_expired_date = db.Column(db.DateTime, nullable=True)
    # Fully disputed date
    fully_disputed_date = db.Column(db.DateTime, nullable=True)

    status  = db.Column(db.String(60), nullable=False) 
    is_active = db.Column(db.Boolean, default=False)

    created_date  = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)


class DebtDisputeLog(db.Model):
    __tablename__ = "debt_dispute_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_on = db.Column(db.DateTime, nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    status  = db.Column(db.String(60), nullable=False) 

    # foreign key
    dispute_id = db.Column(db.Integer, db.ForeignKey('debt_disputes.id', name='debt_dispute_log_dispute_id_fkey'))
    # relationship
    dispute = db.relationship("DebtDispute", backref=backref('logs', cascade="all, delete-orphan"))# foreign key
     
    
