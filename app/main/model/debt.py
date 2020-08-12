from .. import db
from sqlalchemy.orm import backref
from app.main.tasks import mailer 
import enum

class DebtDisputeStatus(enum.Enum):
    # P1 Send
    P1_SEND = 'P1 Send'
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
    debt = db.relationship('DebtCollector', backref='debt_disputes')

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

    # event triggered from timer 
    def on_day_tick(self):
        now = datetime.utcnow()
        if self.status == DebtDisputeStatus.P1_SEND.name or\
           self.status == DebtDisputeStatus.SOLD_PACKAGE_SEND.name:
            diff = (now - self.p1_date) 
            days_expired = diff.days
            # check
            if days_expired > 30:
                # Send Non response notice
                mailer.send_non_response_notice(self.client_id,
                                                self.debt_id,
                                                self.p1_date)
                # Send non response ack
                mailer.send_non_response_ack(self.client_id,
                                             self.debt_id)
                
                self.p2_date = now
                self.status = DebtDisputeStatus.P2_SEND.name 
                self.debt.last_debt_status = DebtDisputeStatus.P2_SEND.value
                db.session.commit()   
        elif self.status == DebtDisputeStatus.P2_SEND.name: 
            diff = (now - self.p2_date)
            days_expired = diff.days
            # more than 20 days
            if days_expired > 20:
                # Send fully disputed ack to client
                mailer.send_fully_dispute_ack(self.client_id,
                                              self.debt_id)
                self.fd_non_response_expired_date = now
                self.status = DebtDisputeStatus.FULLY_DISPUTED_NON_RESPONSE_EXPIRED.name 
                self.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_NON_RESPONSE_EXPIRED.value
                db.session.commit()
        elif self.status == DebtDisputeStatus.NOIR_SEND.name:
            diff = (now - self.noir_date)
            days_expired = diff.days
            if days_expired > 10: 
                mailer.send_fully_dispute_ack(self.client_id,
                                              self.debt_id)
                self.fd_noir_expired_date = now
                self.status = DebtDisputeStatus.FULLY_DISPUTED_NOIR_EXPIRED.name 
                self.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_NOIR_EXPIRED.value
                db.session.commit()
        elif self.status == DebtDisputeStatus.NOIR2_SEND.name:
            diff = (now - self.noir2_date)
            days_expired = diff.days
            if days_expired > 10:
                mailer.send_fully_dispute_ack(self.client_id,
                                              self.debt_id)
                self.fully_disputed_date = now
                self.status = DebtDisputeStatus.FULLY_DISPUTED_EXPIRED.name 
                self.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_NOIR2_EXPIRED.value
                db.session.commit()
        elif self.status == DebtDisputeStatus.NOIR_FDCPA_SEND.name:
            diff = (now - self.noir_fdcpa_date)
            days_expired = diff.days
            if days_expired > 10:
                mailer.send_fully_dispute_ack(self.client_id,
                                              self.debt_id)
                self.fully_disputed_date = now
                self.status = DebtDisputeStatus.FULLY_DISPUTED_EXPIRED.name
                self.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_FDCPA_EXPIRED.value
                db.session.commit()
        elif self.status == DebtDisputeStatus.NOIR_FDCPA_WAIT.name:
            diff = (now - self.fully_disputed_date)
            days_expired = diff.days
            if days_expired > 90:
                self.is_active = False
                db.session.commit() 

    # on collector response 
    def on_collector_response(self):
        now = datetime.utcnow()
        if self.status == DebtDisputeStatus.P1_SEND.name or\
           self.status == DebtDisputeStatus.SOLD_PACKAGE_SEND.name or\
           self.status == DebtDisputeStatus.P2_SEND.name or\
           self.status == DebtDisputeStatus.FULLY_DISPUTED_NON_RESPONSE_EXPIRED.name or\
           self.status == DebtDisputeStatus.FULLY_DISPUTED_NOIR_EXPIRED:
            mailer.send_noir_notice(self.client_id,
                                    self.debt_id) 
            self.noir_date = now
            self.status = DebtDisputeStatus.NOIR_SEND.name  
            self.debt.last_debt_status = DebtDisputeStatus.NOIR_SEND.value
            db.session.commit()
        elif self.status == DebtDisputeStatus.NOIR_SEND.name:
            mailer.send_noir_2_notice(self.client_id,
                                      self.debt_id) 
            self.noir2_date = now
            self.status = DebtDisputeStatus.NOIR2_SEND.name
            self.debt.last_debt_status = DebtDisputeStatus.NOIR2_SEND.value
            db.session.commit()
        elif self.status == DebtDisputeStatus.NOIR2_SEND.name:
            mailer.send_noir_fdcpa_notice(self.client_id,
                                          self.debt_id)
            self.noir_fdcpa_date = now
            self.status = DebtDisputeStatus.NOIR_FDCPA_SEND.name 
            self.debt.last_debt_status = DebtDisputeStatus.FDCPA_SEND.value
            db.session.commit()
        elif self.status == DebtDisputeStatus.NOIR_FDCPA_SEND.name:
            self.status = DebtDisputeStatus.NOIR_FDCPA_WAIT.name 
            db.session.commit()
