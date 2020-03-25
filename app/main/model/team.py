import enum
from app.main import db
from datetime import datetime
from sqlalchemy.orm import backref


class TeamRequestStatus(enum.Enum):
    NEW = 'new'
    APPROVED = 'approved'
    DECLINED = 'declined'
    
class TeamRequestType(db.Model):
    """ db model for storing team request types"""
    __tablename__ = "team_request_types"
    
    # primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)    

    # title & description
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

class TeamRequest(db.Model):
    """ db model for storing team requests"""
    __tablename__ = "team_requests"

    # primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    
    # requested date
    requested_on = db.Column(db.DateTime, default=datetime.utcnow)
    modified_on  = db.Column(db.DateTime, default=datetime.utcnow)
    # requested by 
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id', name='team_requests_requester_id_fkey'))
    account_manager_id = db.Column(db.Integer, db.ForeignKey('users.id', name='team_requests_account_manager_id_fkey'))
    team_manager_id = db.Column(db.Integer, db.ForeignKey('users.id', name='team_requests_team_manager_id_fkey'))
    request_type_id = db.Column(db.Integer, db.ForeignKey('team_request_types.id', name='team_requests_request_type_id_fkey'))
    contract_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id', name='team_requests_contract_id_fkey'))
    
    # relationships
    requester = db.relationship('User', backref='created_requests', foreign_keys=[requester_id])
    account_manager = db.relationship('User', backref='account_requests', foreign_keys=[account_manager_id])
    team_manager = db.relationship('User', backref='team_requests', foreign_keys=[team_manager_id])
    request_type = db.relationship('TeamRequestType', uselist=False, backref='team_request')
    contract = db.relationship('DebtPaymentContract', backref=backref('team_requests', cascade="all, delete-orphan"))

    description = db.Column(db.Text, nullable=True)
    # status
    status =  db.Column(db.Enum(TeamRequestStatus), default=TeamRequestStatus.NEW)
     
## Team Request to notes (1:n)
class TeamRequestNotes(db.Model):
    """ db model for storing team notes""" 
    __tablename__ = "team_request_notes"

    note_id = db.Column(db.Integer, db.ForeignKey('notes.id', name='team_request_notes_note_id_fkey'), primary_key=True)
    team_request_id = db.Column(db.Integer, db.ForeignKey('team_requests.id', name='team_request_notes_team_request_id_fkey'))

    # relationships
    note = db.relationship('Note', backref='team_request_note', uselist=False)
    team_request = db.relationship('TeamRequest', backref='notes')
