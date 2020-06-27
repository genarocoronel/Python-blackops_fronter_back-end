from .. import db

class CandidateDoc(db.Model):
    """ Represents a Candidate Doc """
    __tablename__ = 'candidate_docs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    created_by_username = db.Column(db.String(50), default='System')
    updated_on = db.Column(db.DateTime, nullable=False)
    updated_by_username = db.Column(db.String(50), default='System')

    # Relations
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id', name='fk_doc_candidate_id'))
    candidate = db.relationship('Candidate', backref='candidate_docs')

    type = db.Column(db.String(35)) # See DocprocType. Use string value
    doc_name = db.Column(db.String(100))
    source_channel = db.Column(db.String(25))
    file_name = db.Column(db.String(256))
    orig_file_name = db.Column(db.String(1024))