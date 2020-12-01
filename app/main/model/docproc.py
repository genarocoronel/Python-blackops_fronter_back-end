import enum
from .. import db


class DocprocChannel(enum.Enum):
    """ Represents a Doc Process Source Channel """
    MAIL = 'Mail'
    EMAIL = 'Email'
    FAX = 'Fax'
    SMS = 'SMS'
    PORTAL = 'Portal'
    DSTAR = 'DStar'
    OTHER = 'Other'

class DocprocStatus(enum.Enum):
    """ Represents Doc Process Status """
    NEW = 'New'
    PENDING = 'Pending'
    REJECT = 'Reject'
    WAIT_AM_REVIEW = 'Wait for AM Review'
    APPROVED = 'Approved'
    NEW_REJECT = 'New and Reject'

class DocprocType(db.Model):
    """ Represents Doc Process Types """
    __tablename__ = 'docproc_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String(35))

class DocprocNote(db.Model):
    """ Represents Doc Process Notes """
    __tablename__ = 'docproc_notes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)
    content = db.Column(db.String(1000), nullable=True)
    doc_id = db.Column(db.Integer, db.ForeignKey('docproc.id', name='fk_docproc_notes_doc_id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_docproc_notes_author_user_id'))

    # relationships
    author = db.relationship('User', backref='docproc_notes')


class Docproc(db.Model):
    """ Represents a Document Process """
    __tablename__ = "docproc"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True, nullable=False)
    inserted_on = db.Column(db.DateTime, nullable=False)
    created_by_username = db.Column(db.String(50), default='System')
    updated_on = db.Column(db.DateTime, nullable=False)
    updated_by_username = db.Column(db.String(50), default='System')

    # foreign keys
    type_id = db.Column(db.Integer, db.ForeignKey('docproc_types.id', name='fk_docproc_type_id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='fk_docproc_client_id'), nullable=True)
    docproc_user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_docproc_user_id'), nullable=True)
    accmgr_user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_docproc_accmgr_user_id'), nullable=True)

    # relationships
    type = db.relationship('DocprocType', backref='docproc')
    doc_notes = db.relationship('DocprocNote', backref='docproc')
    client = db.relationship('Client', backref='documents')

    file_name = db.Column(db.String(256))
    orig_file_name = db.Column(db.String(1024))
    doc_name = db.Column(db.String(100))
    source_channel = db.Column(db.String(25))
    correspondence_date = db.Column(db.Date)
    from_who = db.Column(db.String(75))
    debt_name = db.Column(db.String(100))
    creditor_name = db.Column(db.String(75))
    collector_name = db.Column(db.String(75))
    status = db.Column(db.String(75))
    is_published = db.Column(db.Boolean, default=False)
    
