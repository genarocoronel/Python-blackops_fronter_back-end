from app.main.model.debt_payment import DebtPaymentContract
from app.main.model.team import TeamRequest, TeamRequestNote
from app.main.model.usertask import UserTask
from app.main.model.client import Client
from .apiservice import ApiService
from app.main.core.rac import RACRoles

## this file contains Class based services
## function based services -- client_service.py

class ClientService(ApiService):
    _model = Client

    def __init__(self, id=None, public_id=None):
        if id:
            self._client = Client.query.filter_by(id=id).first()
        elif public_id:
            self._client = Client.query.filter_by(public_id=public_id).first()
        # if client is still null
        if not self._client:
            raise ValueError('Client record not found ')

# Client Tasks
class ClientTaskService(ClientService):
    _model = UserTask
    _permissions = [ RACRoles.SUPER_ADMIN, 
                     RACRoles.ADMIN, 
                     RACRoles.SERVICE_ADMIN, 
                     RACRoles.SERVICE_MGR, 
                     RACRoles.SERVICE_REP ]

    def __init__(self, id=None, public_id=None):
        super().__init__(id, public_id)

    def _queryset(self):
        return UserTask.query.filter_by(client_id=self._client.id).all()

# Client Team Requests
class ClientTrService(ClientService):
    _model = TeamRequest
    _permissions = [ RACRoles.SUPER_ADMIN, 
                     RACRoles.ADMIN, 
                     RACRoles.SERVICE_MGR ]

    def __init__(self, id=None, public_id=None):
        super().__init__(id, public_id)

    def _queryset(self):
        return TeamRequest.query.outerjoin(DebtPaymentContract)\
                                .outerjoin(TeamRequestNote)\
                                .filter(DebtPaymentContract.client_id==self._client.id).all()
