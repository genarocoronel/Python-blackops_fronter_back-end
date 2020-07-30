from app.main import db
from app.main.model.usertask import UserTask, TaskStatus, TaskAssignType, TaskPriority, UserTaskNotes
from app.main.model.debt_payment import DebtPaymentContract, ContractStatus, DebtPaymentContractCreditData
from app.main.service.workflow import open_task_flow
from app.main.model.user import User
from app.main.model.client import Client
from app.main.model.notes import Note
from app.main.core.rac import RACRoles, RACMgr
from flask import g
from app.main.service.user_service import get_request_user
from app.main.channels.notification import TaskChannel
from datetime import datetime
import uuid


class UserTaskService(object):
    _qs = None

    def list(self):
        if self._qs:
            return self._qs.all()
        return []

    def get(self):
        return self._qs.first() 

    @classmethod
    def request(cls): 
        obj = cls()
        user = get_request_user()
        agents = [ user ] 
        # if team manager
        for team in user.managed_teams:
            agents = agents + team.agents 
        userids = [user.id for user in agents]
        obj._qs = UserTask.query.filter(UserTask.owner_id.in_(userids)).all()

        return obj

    @classmethod
    def request_user(cls, public_id):
        obj = cls() 
        if not RACMgr.enforce_policy_user_has_role([RACRoles.SERVICE_MGR,]):
            user = get_request_user()
            if user.public_id != public_id:
                return obj

        obj._qs = UserTask.query.outerjoin(User, UserTask.owner)\
                                .filter(User.public_id==public_id)
        return obj

    @classmethod
    def by_id(cls, id):
        obj = cls()
        obj._qs = UserTask.query.filter_by(id=id)
        return obj

    @staticmethod
    def new_task(data):
        user = get_request_user()

        # agent id
        agent_public_id = data.get('assigned_to')
        agent = User.query.filter_by(public_id=agent_public_id).first()       
        if not agent:
            raise ValueError("Assigned to user not found")

        client_id = None
        client_key = data.get('client')
        if client_key:
            client = Client.query.filter_by(public_id=client_key).first()
            client_id = client.id if client else None

        title = data.get('title')
        desc = data.get('description')
        priority = data.get('priority')
        due = data.get('due_date')
        note = data.get('note')
        
        assign_type = TaskAssignType.USER
        task = UserTask(assign_type=assign_type,
                        creator_id=user.id,
                        owner_id=agent.id,
                        priority=priority,
                        title=title,
                        description=desc,
                        due_date=due,
                        client_id=client_id,
                        object_type='UserTask',
                        object_id=None) 

        db.session.add(task)
        db.session.commit()
        # task notes
        add_user_task_notes(task.id, user, note)
        # notify
        TaskChannel.send(agent.id,
                         task)
        return task                          

def update_user_task(task_id, data):
    # fetch the task 
    user_task = UserTask.query.filter_by(id=task_id).first()
    if user_task is None:
        raise ValueError('User task not found')

    # change the due date
    due_date = data.get('due_date')
    if due_date is not None:
        user_task.due_date = due_date

    # change the status
    status = data.get('status')
    if status is not None and status != user_task.status:
        update_user_task_status(user_task, status) 

    # add notes 
    note = data.get('note')
    if note is not None:
        user = get_request_user() 
        add_user_task_notes(task_id, user, note)

    user_task.modified_on = datetime.utcnow()
    db.session.commit()

def update_user_task_status(task, status):
    if status not in TaskStatus.__members__:
        raise ValueError('Not a valid status value')

    tf = open_task_flow(task)
    if tf is not None:
        task_handler = "on_task_{}".format(status.lower())
        func = getattr(tf, task_handler, None)
        if func:
            func(task)

    task.status = status 
    db.session.commit()

def add_user_task_notes(task_id, user, note):
    if not user or not note:
        return None

    note_record = Note(public_id=str(uuid.uuid4()),
                       author_id=user.id,
                       inserted_on=datetime.now(),
                       updated_on=datetime.now(),
                       content=note) 
    db.session.add(note_record)
    db.session.commit()

    task_note = UserTaskNotes(note_id=note_record.id,
                              task_id=task_id)
    db.session.add(task_note)
    db.session.commit()
    
    return task_note
