from .. import db


class BankAccount(db.Model):
    """ Client Bank Account Model """
    __tablename__ = "bank_accounts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))

    # fields
    name = db.Column(db.String(125), nullable=False)
    account_number = db.Column(db.String(100), nullable=False)
    routing_number = db.Column(db.String(100), nullable=False)
    valid = db.Column(db.Boolean, nullable=False)
