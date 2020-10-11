from .. import db


class ContactNumberType(db.Model):
    __tablename__ = "contact_number_types"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)


class ContactNumber(db.Model):
    __tablename__ = "contact_numbers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    contact_number_type_id = db.Column(db.Integer, db.ForeignKey('contact_number_types.id'))

    # fields
    # TODO: refactor model to use BigInteger and migrate data
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    preferred = db.Column(db.Boolean, nullable=False, default=False)

    #relationship
    contact_number_type  = db.relationship("ContactNumberType", backref="contact_numbers") 
