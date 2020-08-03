from app.main import db
from sqlalchemy.orm import backref
from datetime import datetime
import enum


class SalesStatus(enum.Enum):
    ASSIGNED = 'assigned'  # lead assigned
    CONVERTED = 'converted' # converted to deal
    DEAD = 'dead' # inactive
    CLOSED = 'closed' # no futher action by agent

class DistributionHuntType(enum.Enum):
    PRIORITY = 'priority'  # configured priority
    ROUNDROBIN = 'roundrobin' # Round robin
    TIMERATIO = 'timeratio' # lead time ratio

# sales board
class SalesBoard(db.Model):
    """ db model for storing per sales rep stats """
    __tablename__ = "sales_board"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # sales agent
    agent_id  = db.Column(db.Integer, db.ForeignKey('users.id', name='sales_board_agent_id_fkey'))

    # priority based assignments 
    priority = db.Column(db.Integer, default=1) 

    # last assigned date/time
    last_assigned_date = db.Column(db.DateTime, nullable=True) 

    # whether agent is active
    # leads will be distributed only to the active agents
    is_active = db.Column(db.Boolean, default=True)

    # lead distribution stats 
    tot_leads = db.Column(db.Integer, default=0)
    tot_deals = db.Column(db.Integer, default=0)
    # time per lead  
    time_per_lead = db.Column(db.Float, default=0) # minutes

# Sales Flow
# Lead conversion flow
class SalesFlow(db.Model):
    """ db model for storing sales flow information -- assigned to conversion """
    __tablename__ = "sales_flow"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    lead_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='sales_flow_client_id_fkey'))
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id', name='sales_flow_agent_id_fkey')) 

    # relationship
    lead = db.relationship('Client', backref=backref('sales_flow', lazy='dynamic'))
    agent = db.relationship('User', backref=backref('sales_flows', lazy='dynamic'))
    
    assigned_on = db.Column(db.DateTime, nullable=False)
    closed_on = db.Column(db.DateTime, nullable=True)

    status  = db.Column(db.String(40), default=SalesStatus.ASSIGNED.name)
    # num of outbound calls
    num_out_calls = db.Column(db.Integer, default=0)
    # call duration
    call_duration = db.Column(db.Integer, default=0)
    # recycled lead
    is_recycled = db.Column(db.Boolean, default=False)


class LeadDistributionProfile(db.Model):
    """ db model for storing lead distribution config """
    __tablename__ = "lead_distribution_profile"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    hunt_type = db.Column(db.String(40), default=DistributionHuntType.PRIORITY.name) 
    flow_interval = db.Column(db.Integer, default=10) # minutes
    language = db.Column(db.String(40), default='ENGLISH')
    
    # last added board
    last_added_id = db.Column(db.Integer, db.ForeignKey('sales_board.id', name='lead_distribution_profile_last_added_id_fkey'))
