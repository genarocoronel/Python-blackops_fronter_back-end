import enum

from .. import db


class AddressType(enum.Enum):
    CURRENT = 'CURRENT'
    PAST = 'PAST'


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    address1 = db.Column(db.String(100), nullable=False)
    address2 = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(20), nullable=False)
    from_date = db.Column(db.Date())
    to_date = db.Column(db.Date())
    type = db.Column(db.Enum(AddressType), nullable=False)
