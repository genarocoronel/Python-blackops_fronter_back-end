from .. import db
from sqlalchemy.orm import backref


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
    debt = db.relationship('CreditReportData', backref=backref('disputes', lazy='dynamic'))

    # p1 received date
    p1_date = db.Column(db.DateTime, nullable=True)
    # p2 received date
    p2_date = db.Column(db.DateTime, nullable=True)
    # NOIR received date
    noir_date = db.Column(db.DateTime, nullable=True)
    # SP received date
    sp_date = db.Column(db.DateTime, nullable=True)
    # Fully disputed date
    fully_disputed_date = db.Column(db.DateTime, nullable=True)


    modified_date = db.Column(db.DateTime, nullable=False)
