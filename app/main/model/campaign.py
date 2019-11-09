from app.main import db


class Campaign(db.Model):
    """ Campaign Model """
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # relationships
    candidates = db.relationship('Candidate', back_populates='campaign')

    # fields
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(25), nullable=False)
