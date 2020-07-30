from sqlalchemy import asc
from app.main.model.user import User
from app.main.model.sales_board import SalesBoard, LeadDistributionProfile, DistributionHuntType
from app.main.model import Language
from app.main import db


class LeadDistroSvc(object):
    _hunt_type = DistributionHuntType.PRIORITY.name
    _flow_interval = 10

    def __init__(self, lang=Language.ENGLISH.name):
        self._load_profile(lang) 
    
    # fetch users by priority
    def get(self):
        users = User.query.outerjoin(SalesBoard)\
                          .filter(User.id==SalesBoard.agent_id)\
                          .order_by(asc(SalesBoard.priority)).all()
        result = {
            'agents': users,
            'hunt_type': self._hunt_type,
            'flow_interval': self._flow_interval,
        }
        return result
 
    # change the priorities 
    def update(self, data):
        agents = data.get('agents')
        print(agents)
        priority = 0
        for agent in agents:
            priority = priority + 1
            user = User.query.filter_by(public_id=agent['id']).first()  
            if user.sales_board:
                user.sales_board.priority = priority
                user.sales_board.is_active = agent['is_active']
            db.session.commit()
 
        result = {
            'success': True,
            'message': 'Lead Distribution priorities changed scuccessfully',
        }

        return result

        
    def _load_profile(self, lang):
        # fetch the profile 
        profile = LeadDistributionProfile.query.filter_by(language=lang).first() 
        if profile:
            self._hunt_type = profile.hunt_type
            self._flow_interval = profile.flow_interval

