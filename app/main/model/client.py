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
    first_name = db.Column(db.String(25), nullable=False)
    middle_initial = db.Column(db.CHAR, nullable=True)
    suffix = db.Column(db.String(25), nullable=True)
    address = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zip = db.Column(db.Integer, nullable=False)
    zip4 = db.Column(db.Integer, nullable=False)
    county = db.Column(db.String(50), nullable=False)
    crrt = db.Column(db.String(4), nullable=False)
    dpbc = db.Column(db.Integer, nullable=False)
    fips = db.Column(db.Integer, nullable=False)
    estimated_debt = db.Column(db.Integer, nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    language = db.Column(db.String(25), nullable=True)
    phone = db.Column(db.String(25), nullable=True)
    type = db.Column(db.Enum(ClientType), nullable=False, default=ClientType.lead)
    public_id = db.Column(db.String(100), unique=True)

    # def __hash__(self):
    #     return hash(self.first_name, self.last_name, self.address, self.city, self.zip)
    #
    # def __eq__(self, other):
    #     if isinstance(other, type(self)):
    #         return self.__hash__() == other.__hash__()
    #     return NotImplemented
