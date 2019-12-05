import enum

from .. import db

class Employment(db.Model):
    __tablename__ = "employments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys

    # relationships

    # fields
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    gross_salary = db.Column(db.Float, nullable=False)
    gross_salary_frequency = db.Column(db.Enum(FrequencyStatus), nullable=True, default=FrequencyStatus.MONTHLY)
    other_income = db.Column(db.Float, nullable=False)
    other_income_frequency = db.Column(db.Enum(FrequencyStatus), nullable=True, default=FrequencyStatus.MONTHLY)
    current = db.Column(db.Boolean, default=False)

class FrequencyStatus(enum.Enum):
    ANNUAL = 'annual'
    MONTHLY = 'monthly'