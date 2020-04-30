from app.main import db
from app.main.model.usertask import UserTask, TaskStatus
from app.main.model.debt_payment import DebtPaymentContract, ContractStatus, DebtPaymentContractCreditData
from app.main.service.workflow import open_task_flow
from datetime import datetime

def fetch_user_tasks(user):
    user_tasks = UserTask.query.filter_by(owner_id=user.id).all()
    
    return user_tasks 

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
    
