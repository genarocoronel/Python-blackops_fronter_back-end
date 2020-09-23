import enum
from .. import db


class Auditable(enum.Enum):
    CANDIDATE = "candidate"
    LEAD = "lead"
    CLIENT = "client"
    USER = "user"


class Audit(db.Model):
    """ Represents an Audit """
    __tablename__ = "audit"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)

    auditable = db.Column(db.String(25))
    auditable_subject_pubid = db.Column(db.String(100))
    action = db.Column(db.String(100))
    requestor_username = db.Column(db.String(20))
    message = db.Column(db.String(140))
    is_internal = db.Column(db.Boolean, default=False)

    requestor_id = db.Column(db.Integer, db.ForeignKey('users.id', name='audit_requestor_id_fkey'))
    requestor = db.relationship('User', backref='audited_items')
