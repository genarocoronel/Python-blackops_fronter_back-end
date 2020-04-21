from .. import db

class DebtCollector(db.Model):
    """ Represents a Debt Collector """
    __tablename__ = "debt_collectors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)
    created_by_username = db.Column(db.String(50), default='System')
    updated_on = db.Column(db.DateTime)
    updated_by_username = db.Column(db.String(50), default='System')

    name = db.Column(db.String(100))
    phone = db.Column(db.String(10))
    fax = db.Column(db.String(10))
    address = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(5))