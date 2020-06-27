# support ticket from the clients
import enum
from app.main import db
from datetime import datetime

class TicketPriority(enum.Enum):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'

class TicketStatus(enum.Enum):
    OPEN = 'open'
    PENDING = 'pending'
    RESOLVED = 'resolved'
    CLOSED = 'closed'

class TicketSource(enum.Enum):
    WEB_PORTAL = 'webportal'
    EMAIL = 'email'
    PHONE = 'phone'

class Ticket(db.Model):
    """ db model for storing support tickets"""
    __tablename__ = "tickets"
    # primary key 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    modified_on = db.Column(db.DateTime, default=datetime.utcnow)

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', name='tickets_owner_id_fkey'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='tickets_client_id_fkey'))

    owner = db.relationship('User', backref='assigned_tickets', foreign_keys=[owner_id])
    client = db.relationship('Client', backref='support_tickets')

    # priority, status
    priority = db.Column(db.String(40), default=TicketPriority.MEDIUM.name)
    status = db.Column(db.String(40), default=TicketStatus.OPEN.name)
    source = db.Column(db.String(40), default=TicketSource.EMAIL.name)

    title = db.Column(db.String(120), nullable=False)
    # ticket description
    desc = db.Column(db.String(200), nullable=True)

