import uuid
from app.main import db
from app.main.model.team import TeamRequest, TeamRequestStatus, TeamRequestNotes
from app.main.model.debt_payment import DebtPaymentContract
from app.main.model.client import Client
from app.main.model.notes import Note
from app.main.util.decorator import enforce_rac_required_roles
from app.main.core.rac import RACRoles
from flask import g
from datetime import datetime

# fetch team requests for a team
# @enforce_rac_required_roles(['service_mgr'])
@enforce_rac_required_roles([RACRoles.SERVICE_MGR,])
def fetch_team_requests(team_name):
    team_requests = TeamRequest.query.outerjoin(DebtPaymentContract)\
                                     .outerjoin(Client).all()
    return team_requests

def filter_team_requests(user):
    team_requests = TeamRequest.query.filter_by(team_manager_id=user.id).all()
    return team_requests

# update team requests
@enforce_rac_required_roles([RACRoles.SERVICE_MGR,])
def update_team_request(team_request_id, data):
    # fetch the team request based on ID
    team_request = TeamRequest.query.filter_by(public_id=team_request_id).first()
    if team_request is None:
        raise ValueError('Team request not found') 

    # notes 
    note = data.get('note', None)
    if note is not None and note.strip() != '': 
        add_team_request_notes(team_request, note)

    # check for status change
    status = data.get('status', None)
    if team_request.status != status:
        change_team_request_status(team_request, status)
 
    team_request.modified_on = datetime.utcnow()
    db.session.commit()

    return {
        'success': True,
        'message': 'Status Changed'
    }
       

def change_team_request_status(team_request, status):

    if status not in TeamRequestStatus.__members__:
        raise ValueError('Not a valid status name')

    obj = None
    state_handler = "ON_TR_{}".format(status)
    obj = team_request.contract
    if obj is not None:
        try:
            func = getattr(obj, state_handler)
            # call the state handler
            func(team_request)
        except Exception as err:
            # state handler is not defined
            pass
    
    team_request.status = status
    db.session.commit()

def add_team_request_notes(team_request, note ):
    user = g.current_user 
    note_record = Note(public_id=str(uuid.uuid4()),
                       inserted_on=datetime.utcnow(),
                       updated_on=datetime.utcnow(),
                       author_id=user['user_id'],
                       content=note)  
    db.session.add(note_record)
    db.session.commit()

    # realtional table
    trn = TeamRequestNotes(note_id=note_record.id,
                           team_request_id=team_request.id)
    db.session.add(trn)
    db.session.commit()

     
