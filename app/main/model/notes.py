from .. import db

class Note(db.Model):
    """ Note by User """
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))

    # fields
    content = db.Column(db.String(1000), nullable=True)
