from app.main.model import Frequency
from .. import db


class IncomeType(db.Model):
    __tablename__ = 'income_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)


class Income(db.Model):
    __tablename__ = 'income_sources'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    income_type_id = db.Column(db.Integer, db.ForeignKey('income_types.id'))

    # fields
    value = db.Column(db.Integer, nullable=False)
    frequency = db.Column(db.Enum(Frequency), nullable=False, default=Frequency.MONTHLY)
