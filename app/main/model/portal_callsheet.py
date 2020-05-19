import enum
from .. import db


class PortalCallsheet(db.Model):
    """ Represents a Portal Callsheet """
    __tablename__ = 'portal_callsheet'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)
    
    callsheet_date = db.Column(db.DateTime, nullable=False)
    is_orig_creditor = db.Column(db.Boolean, default=False)
    is_hardship_call = db.Column(db.Boolean, default=False)
    debt_name = db.Column(db.String(75))
    creditor_name = db.Column(db.String(75))
    collector_name = db.Column(db.String(75))
    received_from_phone_number = db.Column(db.String(20))
    received_on_phone_type = db.Column(db.String(10))
    notes = db.Column(db.String(918))
    is_file_attached = db.Column(db.Boolean, default=False)

    # Relationships
    portal_user_id = db.Column(db.Integer, db.ForeignKey('portal_users.id', name='fk_portal_callsheets_portal_users_id'))
    docproc_id = db.Column(db.Integer, db.ForeignKey('docproc.id', name='fk_portal_callsheets_docproc_id'), nullable=True)

