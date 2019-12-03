import enum

from .. import db


class ClientType(enum.Enum):
    candidate = "candidate"
    lead = "lead"
    client = "client"


class Client(db.Model):
    """ Client Model for storing client related details """
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # relationships
    bank_account = db.relationship('BankAccount', uselist=False, backref='client')

    # fields
    suffix = db.Column(db.String(25), nullable=True)
    first_name = db.Column(db.String(25), nullable=False)
    middle_initial = db.Column(db.CHAR, nullable=True)
    last_name = db.Column(db.String(25), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zip = db.Column(db.Integer, nullable=False)
    zip4 = db.Column(db.Integer, nullable=False)
    estimated_debt = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    language = db.Column(db.String(25), nullable=True)
    phone = db.Column(db.String(25), nullable=True)
    type = db.Column(db.Enum(ClientType), nullable=False, default=ClientType.lead)
