import enum
from app.main import db
from datetime import datetime

class TaskPriority(enum.Enum):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'

class TaskStatus(enum.Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'

class TaskAssignType(enum.Enum):
    AUTO = 'Automatic'
    USER = 'Manual'

class UserTask(db.Model):
    """ db model for storing user tasks"""
    __tablename__ = "user_tasks"

    # primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.utcnow)

    assign_type = db.Column(db.Enum(TaskAssignType), default=TaskAssignType.AUTO)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', name='user_tasks_creator_id_fkey'))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', name='user_tasks_owner_id_fkey'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='user_tasks_client_id_fkey'))

    # relationships
    owner = db.relationship('User', backref='own_tasks', foreign_keys=[owner_id])
    creator = db.relationship('User', backref='created_tasks', foreign_keys=[creator_id])
    client = db.relationship('Client', backref='user_tasks')
   
    # priority, status 
    priority = db.Column(db.String(40), default=TaskPriority.MEDIUM.name)
    status = db.Column(db.String(40), default=TaskStatus.PENDING.name)

    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    # non expire tasks (null=True)
    due_date = db.Column(db.DateTime, nullable=True)

    # business object associated with task
    object_type = db.Column(db.String(120), nullable=True)
    object_id   = db.Column(db.Integer, nullable=True)

## User Task  notes (1:n)
class UserTaskNotes(db.Model):
    """ db model for storing team notes"""
    __tablename__ = "user_task_notes"

    note_id = db.Column(db.Integer, db.ForeignKey('notes.id', name='user_task_notes_note_id_fkey'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('user_tasks.id', name='user_task_notes_task_id_fkey'))

    # relationships
    note = db.relationship('Note', backref='task_note', uselist=False)
    task = db.relationship('UserTask', backref='notes')
