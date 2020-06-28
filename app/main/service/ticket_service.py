from app.main.core.errors import ForbiddenError, NotFoundError
from app.main.model.ticket import Ticket, TicketPriority, TicketStatus, TicketSource
from app.main import db
from flask import g

from app.main.model.user import User
from app.main.model.client import Client
from app.main.channels.notification import TicketChannel
from app.main.model.rac import RACRole
from app.main.core.rac import RACRoles
from app.main.model.portal_user import *


class TicketService(object):
    _permissions = []

    def _is_allowed(self):
        # allow all
        if len(self._permissions) == 0:
            return True

        user_role = self._user['rac_role']
        for permitted_role in self.__permissions:
            if user_role == permitted_role.value:
                return True

        return False

    def _create(self, data):
        # check for the permissions
        if not self._is_allowed():
            raise ForbiddenError("Resource not allowed")

        obj = Ticket() 
        for attr in data:
            if hasattr(obj, attr): 
                setattr(obj, attr, data.get(attr))

        obj.priority = self._priority.name
        obj.source  = self._source.name
        obj.title = self._title
        obj.client = self._client
        obj.owner  = self._assigned_to

        db.session.add(obj)
        db.session.commit()
        return obj

    def update(self, key, data):
        # check for the permissions
        if not self._is_allowed():
            raise ForbiddenError("Resource not allowed")

        obj = Ticket.query.filter_by(id=key).first() 
        for attr in data:
            if hasattr(obj, attr): 
                setattr(obj, attr, data.get(attr))

        db.session.commit()
        return obj

    def get(self):
        # check for the permissions
        if not self._is_allowed():
            raise ForbiddenError("Resource not allowed")

        qs = self.queryset()
        return qs

# ticket creation from the portal
class PortalNewTicket(TicketService):
    _priority = TicketPriority.CRITICAL
    _source  = TicketSource.WEB_PORTAL
    
    def open(self, data):
        code = data.get('code')
        # ticket reason
        if 'CONNECT_SUPERVISOR' in code:
            self._title = 'Escalate to Supervisor' 
        # requested client
        user = g.current_portal_user
        #user = {'user_id': 1}
        puser = PortalUser.query.filter_by(public_id=user['public_id']).first()
        client = puser.client
        if client is None:
            raise NotFoundError("Client not found")
        self._client = client
        # assign to supervisor 
        # todo: get from the client profile
        svc_mgr = User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
        self._assigned_to = svc_mgr

        ticket = self._create(data)
        ## Notify service manager
        TicketChannel.send(svc_mgr.id, 
                           ticket)
        return ticket

class PortalOpenedTickets(TicketService):
    
    def queryset(self):
        req_user = g.current_portal_user
        portal_user = PortalUser.query.filter_by(public_id=req_user['public_id']).first()	
        if not portal_user:
            raise NotFoundError("User not found")
        qs = Ticket.query.filter_by(client_id=portal_user.client.id).all()
        return qs
        
    
class AssignedTickets(TicketService):
    def queryset(self):
        req_user = g.current_user
        user = User.query.filter_by(id=req_user['user_id']).first()
        if not user:
            raise NotFoundError("User not found")
        qs = Ticket.query.filter_by(owner_id=user.id).all()
        return qs
