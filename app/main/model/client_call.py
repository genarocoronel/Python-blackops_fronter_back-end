import enum
from datetime import datetime
from .. import db


class CallStatus(enum.Enum):
    Planned = "planned"
    Ongoing = "ongoing"
    Success = "success"
    Rejected = "rejected"
    Failed = "failed"


class CallDirection(enum.Enum):    
    Incoming = "incoming"
    Outgoing = "outgoing"


class ClientCall(db.Model):
    """ model for storing client calls deta"""
    __tablename__ = "client_calls"
   
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    # called agent id 
    agent_id  = db.Column(db.Integer, db.ForeignKey('users.id'))

    #relationships
    client = db.relationship('Client', backref='calls') 
    agent = db.relationship('User', backref='client_calls') 

    # Call start & end date time
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    # duration in mins
    duration_mins = db.Column(db.Integer, nullable=True)
    
    status = db.Column(db.Enum(CallStatus), nullable=True, default=CallStatus.Planned)
    direction = db.Column(db.Enum(CallDirection), nullable=False, default=CallDirection.Outgoing)


    @classmethod
    def create(cls, **kwargs):
        try:
            end = datetime.now()
            hrs = 0
            mins = 0

            if 'start_date' in kwargs:
                start = kwargs['start_date']
                if 'end_date' in kwargs:
                    end = kwargs['end_date']
                diff  = (end - start)  
                mins = int(diff.seconds / 60) 
               
            kwargs['duration_mins'] = mins
            obj = cls(**kwargs)
            db.session.add(obj)      
            db.session.commit()
        except Exception as err:
            db.session.rollback()
            
