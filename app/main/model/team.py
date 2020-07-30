import enum
from app.main import db
from datetime import datetime
from sqlalchemy.orm import backref

class TeamRequestStatus(enum.Enum):
    NEW = 'new'
    APPROVED = 'approved'
    DECLINED = 'declined'

class Team(db.Model):
    """ db model for storing team details """
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # team manager
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id', name='teams_manager_id_fkey'))
    manager = db.relationship('User', backref='managed_teams', foreign_keys=[manager_id]) 
    # team creator
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', name='teams_creator_id_fkey'))
    creator = db.relationship('User', backref=backref('created_teams', lazy="dynamic"), foreign_keys=[creator_id]) 
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date  = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def members(self):
        return [tm.member for tm in self.team_members]

    
class TeamMember(db.Model):
    """ db model for storing team members"""
    __tablename__ = "team_members"

    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', name="team_members_team_id_fkey"), primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('users.id', name='team_members_member_id_fkey'), primary_key=True)

    team = db.relationship('Team', backref='team_members')

    created_date = db.Column(db.DateTime, nullable=False)


class TeamRequestType(db.Model):
    """ db model for storing team request types"""
    __tablename__ = "team_request_types"
    
    # primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)    

    # title & description
    code =  db.Column(db.String(80), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    doc_sign_required = db.Column(db.Boolean, default=True)


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
    # contract revision
    revision_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract_revision.id', name='team_requests_revision_id_fkey'))
    
    # relationships
    requester = db.relationship('User', backref='created_requests', foreign_keys=[requester_id])
    account_manager = db.relationship('User', backref='account_requests', foreign_keys=[account_manager_id])
    team_manager = db.relationship('User', backref='team_requests', foreign_keys=[team_manager_id])
    request_type = db.relationship('TeamRequestType', uselist=False, backref='team_request')
    contract = db.relationship('DebtPaymentContract', backref=backref('team_requests', cascade="all, delete-orphan"))
    revision = db.relationship('DebtPaymentContractRevision', backref=backref('team_requests', cascade="all, delete-orphan"))

    description = db.Column(db.Text, nullable=True)
    # status
    status =  db.Column(db.Enum(TeamRequestStatus), default=TeamRequestStatus.NEW)
     
## Team Request to notes (1:n)
class TeamRequestNote(db.Model):
    """ db model for storing team notes""" 
    __tablename__ = "team_request_notes"

    note_id = db.Column(db.Integer, db.ForeignKey('notes.id', name='team_request_notes_note_id_fkey'), primary_key=True)
    team_request_id = db.Column(db.Integer, db.ForeignKey('team_requests.id', name='team_request_notes_team_request_id_fkey'))

    # relationships
    note = db.relationship('Note', uselist=False, backref=backref('team_request_note', cascade="all, delete-orphan"))
    team_request = db.relationship('TeamRequest', backref=backref('notes', cascade="all, delete-orphan"))
