from app.main import db
from app.main.model.usertask import UserTask, TaskStatus
from app.main.model.debt_payment import DebtPaymentContract, ContractStatus, DebtPaymentContractCreditData
from app.main.service.workflow import open_task_flow
from app.main.model.user import User, Department
from app.main.core.rac import RACRoles, RACMgr
from flask import g
from app.main.service.user_service import get_request_user
from datetime import datetime


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
        # role based access
        if RACMgr.enforce_policy_user_has_role([RACRoles.SERVICE_MGR,]):
            obj._qs = UserTask.query.outerjoin(User, UserTask.owner)\
                                    .filter(User.department == Department.SERVICE.name)
        else:    	
            obj._qs = UserTask.query.filter_by(owner_id=user.id)
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
        add_user_task_notes(task_id, note)

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

def add_user_task_notes(task_id, note):
    # user = g.current_user 
    note_record = Note(public_id=str(uuid.uuid4()),
                       authord_id=user['id'],
                       content=note) 
    db.session.add(note_record)
    db.session.commit()

    task_note = UserTaskNote(note_id=note_record.id,
                             task_id=task_id)
    db.session.add(task_note)
    db.session.commit()
    
