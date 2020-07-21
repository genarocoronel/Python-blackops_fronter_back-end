from app.main import db
from datetime import datetime


class Creditor(db.Model):
    """ Creditor Model for storing creditor related details """
    __tablename__ = "creditors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # created date
    inserted_on = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(100), unique=True)

    company_name = db.Column(db.String(100), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(16), nullable=True)
    fax = db.Column(db.String(16), nullable=True)
    email = db.Column(db.String(254), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    updated_on = db.Column(db.DateTime, default=datetime.utcnow)

    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(60), nullable=True)
    state = db.Column(db.String(60), nullable=True)
    zipcode = db.Column(db.String(10), nullable=True)
