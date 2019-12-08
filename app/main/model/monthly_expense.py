from .. import db


class ExpenseType(db.Model):
    __tablename__ = 'expense_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)


class MonthlyExpense(db.Model):
    __tablename__ = 'monthly_expenses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    expense_type_id = db.Column(db.Integer, db.ForeignKey('expense_types.id'))

    # fields
    value = db.Column(db.Integer, nullable=False)
