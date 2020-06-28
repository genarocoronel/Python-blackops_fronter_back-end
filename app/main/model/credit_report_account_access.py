from .. import db

class CreditReportAccountAccess(db.Model):
    """ Represents a SCredit Report Acc access log """
    __tablename__ = 'credit_report_account_access'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    accesed_by_username = db.Column(db.String(50), default='System')
    was_allowed = db.Column(db.Boolean, nullable=False)
    # No foreign key in log by design
    credit_report_account_id = db.Column(db.Integer, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)

