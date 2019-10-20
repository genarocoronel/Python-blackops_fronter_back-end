from .. import db


class Client(db.Model):
    """ Client Model for storing client related details """
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    language = db.Column(db.String(25), nullable=False)
    phone = db.Column(db.String(25), nullable=False)
    public_id = db.Column(db.String(100), unique=True)
