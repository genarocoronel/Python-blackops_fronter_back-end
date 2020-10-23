import enum

from .. import db

class MilitaryOptions(enum.Enum):
    NOT_MILITARY = "not_military"
    ACTIVE_RESERVE = "active_reserve"
    VETERAN = "veteran" 
    DEPENDENT_OF_ACTIVE = "dependent_of_active" 

class ResidencyOptions(enum.Enum):
    US_CITIZEN = "us_citizen"
    TEMP_RESIDENT_VISA = "temp_resident_visa"
    PERMANENT_RESIDENT = "permanent_resident"
    NON_RESIDENT = "non_resident"

class EmploymentOptions(enum.Enum):
    FULL_TIME = "full_time"
    SELF_EMPLOYED = "self_employed"
    RETIRED = "retired"
    PART_TIME = "part_time"
    UNEMPLOYED = "unemployed"
    OTHER = "other"

class PayFrequencyOptions(enum.Enum):
    BI_WEEKLY = 'bi_weekly'
    TWICE_A_MONTH = 'twice_a_month'
    MONTHLY = 'monthly'
    WEEKLY = 'weekly'
    OTHER = 'other'

class PayMethodOptions(enum.Enum):
    DIRECT_DEPOSIT = "direct_deposit"
    MISC_INCOME = "misc_income"
    PAYROLL_PREPAID = "payroll_prepaid"
    CASH_OTHER = "cash_other"

class SupermoneyOptions(db.Model):
    __tablename__ = "supermoney_options"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))

    military_status = db.Column(db.Enum(MilitaryOptions), nullable=True)
    residency_status = db.Column(db.Enum(ResidencyOptions), nullable=True)
    employment_status = db.Column(db.Enum(EmploymentOptions), nullable=True)
    pay_frequency = db.Column(db.Enum(PayFrequencyOptions), nullable=True)
    pay_method = db.Column(db.Enum(PayMethodOptions), nullable=True)
    checking_account = db.Column(db.Boolean, nullable=True)