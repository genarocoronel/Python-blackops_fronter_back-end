from sqlalchemy import asc
from app.main.model.user import User
from app.main.model.sales_board import SalesBoard, SalesFlow, SalesStatus, LeadDistributionProfile, DistributionHuntType
from app.main.model import Language
from app.main import db
from flask import current_app as app
from datetime import datetime
from sqlalchemy import desc


class LeadDistroSvc(object):
    _profile = None

    def __init__(self, lang=Language.ENGLISH.name):
        self._load_profile(lang) 
    
    # fetch users by priority
    def get(self):
        sales_boards = SalesBoard.query.order_by(asc(SalesBoard.priority)).all()
        # Fetch the assignment history
        assigned_records = SalesFlow.query.order_by(desc(SalesFlow.assigned_on)).limit(10).all() 
        result = {
            'sales_boards': sales_boards,
            'assigned_history': assigned_records,  
            'hunt_type': self._profile.hunt_type,
            'flow_interval': self._profile.flow_interval,
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

        # user
        if user:
            self._profile.last_added_id = user.sales_board.id
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
            self._profile = profile


    def _fetch_by_priority(self, lead):
        try:
            boards = SalesBoard.query.filter_by(is_active=True)\
                                     .order_by(asc(SalesBoard.priority))\
                                     .order_by(asc(SalesBoard.tot_leads)).all()
            if len(boards) == 0:
                return None

            sales_board = None
            # only one sales person or already assigned til last in queue
            if len(boards) == 1 or\
               boards[-1].id == self._profile.last_added_id or\
               self._profile.last_added_id == None:
                # assign 
                sales_board = boards[0]
            else:
                assign_next = False
                for board in boards:
                    if assign_next == True:
                        sales_board = board
                        break
                    if board.id == self._profile.last_added_id:
                        assign_next = True

            return sales_board

        except Exception as err:
            # failed
            app.logger.warning("Failed to fetch agent by priority {}".format(str(err)))
            return None

    # round robin
    def _fetch_by_rrobin(self):
        try:
            sales_board = None
            now = datetime.utcnow()
            boards = SalesBoard.query.filter_by(is_active=True)\
                                     .order_by(asc(SalesBoard.tot_leads)).all()
            for board in boards:
                diff = now - board.last_assigned_date 
                profile = self._profile
                if diff.seconds > profile.flow_interval:
                    sales_board = board
                    break

            return sales_board
            

        except Exception as err:
            # failed
            app.logger.warning("Failed to fetch agent by round robin {}".format(str(err)))
            return None

    # time ratio
    def _fetch_by_timeratio(self):
        try:
           sales_board = None
           now = datetime.utcnow()
           boards = SalesBoard.query.filter_by(is_active=True)\
                                    .order_by(asc(SalesBoard.time_per_lead)).all()
           for board in boards:
               diff = now - board.last_assigned_date 
               profile = self._profile
               if diff.seconds > profile.flow_interval:
                   sales_board = board
                   break

           return sales_board

        except Exception as err:
           # failed
           app.logger.warning("Failed to fetch agent by time ratio {}".format(str(err)))
           return None

             
    def assign_lead(self, lead):
        try:
            sales_board = None

            if self._profile.hunt_type == DistributionHuntType.PRIORITY.name:
                sales_board = self._fetch_by_priority(lead)
            elif self._profile.hunt_type == DistributionHuntType.ROUNDROBIN.name:
                sales_board = self._fetch_by_rrobin(lead)
            elif self._profile.hunt_type == DistributionHuntType.TIMERATIO.name:
                sales_board = self._fetch_by_timeratio(lead)
            
            sales_agent = sales_board.agent 

            # create a sales flow
            sflow = SalesFlow(lead_id=lead.id,
                              agent_id=sales_agent.id,
                              assigned_on=datetime.utcnow())
            db.session.add(sflow)

            # update the sales profile
            self._profile.last_added_id = sales_board.id 
            # update sales board
            sales_board.tot_leads = sales_board.tot_leads + 1
            sales_board.last_assigned_date = datetime.utcnow()
            # update lead
            lead.sales_rep_id = sales_agent.id

            db.session.commit()

            return sales_agent
         
        except Exception as err:
            app.logger.warning("Failed to assign lead {}".format(str(err)))
            return None

    def on_manual_assign(self, lead, user):
        try:
            old_sf = SalesFlow.query.filter_by(lead_id=lead.id,
                                               status=SalesStatus.ASSIGNED.name).first()
            if old_sf:
                old_sf.status = SalesStatus.REASSIGNED.name 

            new_sf = SalesFlow(lead_id=lead.id,
                               agent_id=user.id,
                               assigned_on=datetime.utcnow())
            db.session.add(new_sf)

            sales_board = SalesBoard.query.filter_by(agent_id=user.id).first()
            if sales_board:
                sales_board.tot_leads = sales_board.tot_leads + 1
                sales_board.last_assigned_date = datetime.utcnow()
            db.session.commit()

        except Exception as err:
             app.logger.warning("Failed in manual assign lead {}".format(str(err)))
             return None
            
