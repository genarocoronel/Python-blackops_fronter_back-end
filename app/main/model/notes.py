from .. import db


class CandidateNote(db.Model):
    __tablename__ = "candidate_notes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # foreign keys
    candidate_id = db.relationship(db.Integer, db.ForeignKey('candidates.id'))
    author_id = db.relationship(db.Integer, db.ForeignKey('users.id'))

    # fields
    category = db.Column(db.String, nullable=False)
    content = db.Column(db.TEXT, nullable=False)
