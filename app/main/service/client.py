from app.main.model.debt_payment import DebtPaymentContract, ContractStatus, DebtPaymentSchedule, DebtEftStatus
from app.main.model.team import TeamRequest, TeamRequestType, TeamRequestNote
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority
from app.main.model.client import Client, ProgramStatus
from app.main.model.user import User
from app.main.model.rac import RACRole
from app.main.model.audit import Audit, Auditable
from app.main.core.rac import RACRoles
from .apiservice import ApiService
from app.main.channels.notification import TaskChannel, TeamRequestChannel
from flask import current_app as app
from datetime import datetime, timedelta
from sqlalchemy import and_
from app.main import db
import enum
import uuid

## this file contains Class based services
## function based services -- client_service.py
class ClientAction(enum.Enum):
    DEAL_COMPLETE = 'Deal Complete'
    DEAL_REJECT   = 'Deal Reject'

class ClientService(ApiService):
    _model = Client

    def __init__(self, client=None, id=None, public_id=None):
        if client:
            self._client = client
        elif id:
            self._client = Client.query.filter_by(id=id).first()
        elif public_id:
            self._client = Client.query.filter_by(public_id=public_id).first()
        # if client is still null
        if not self._client:
            raise ValueError('Client record not found ')
        super().__init__()

    # cancellation request
    def on_add2retention(self):
        if not self._client:
            raise ValueError('Client not found')
        client = self._client
        # check the status 
        program_status = client.program_status
        if (program_status == ProgramStatus.SIGNED.name) or\
           (program_status == ProgramStatus.ACTIVE.name):
            # check if request cancel is already processed
            if 'Sales_ActiveStatus_RequestCancellationInit' not in client.status_name:
                user = self._req_user
                if client.account_manager:
                    user = client.account_manager

                # send request cancellation email
                app.queue.enqueue('app.main.tasks.mailer.send_cancellation_request',
                                   client.id, failure_ttl=300)

                # create a task to call client
                due = datetime.utcnow() + timedelta(hours=24)
                task = UserTask(assign_type=TaskAssignType.AUTO,
                                owner_id=user.id, 
                                priority=TaskPriority.MEDIUM.name,
                                title='Call Client',
                                description='Call Client: Confirm Request Cancellation',
                                due_date=due,
                                client_id=self._client.id,
                                object_type='Client',
                                object_id=self._client.id)
                db.session.add(task)
                # notify the task
                TaskChannel.send(user.id,
                                 task) 
                # check if payment is already processed
                dps = DebtPaymentSchedule.query.outerjoin(DebtPaymentContract)\
                                               .filter(and_(DebtPaymentContract.client_id==client.id, DebtPaymentSchedule.status==DebtEftStatus.SEND_TO_EFT.name)).first()                
                if dps is not None:
                    stop_pymt_task = UserTask(assign_type=TaskAssignType.AUTO,
                                             owner_id=user.id,
                                             priority=TaskPriority.MEDIUM.name,
                                             title='Call the drafting company and stop the payment',
                                             description='Calll drafting company and stop the payment',
                                             due_date=due,
                                             client_id=client.id,
                                             object_type='Client',
                                             object_id=client.id)
                    db.session.add(stop_pymt_task)
                    TaskChannel.send(user.id,
                                     stop_pymt_task) 

                # pause the future payments
                contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                               status=ContractStatus.ACTIVE).first()
                if contract is not None:
                    for sch in  contract.payment_schedule:
                        if sch.status == DebtEftStatus.FUTURE.name:
                            sch.status = DebtEftStatus.PAUSED.name
                # change the status
                client.status_name = 'Sales_ActiveStatus_RequestCancellationInitiated'
                db.session.commit()

    
    def on_disposition_change(self, disposition):
        client = self._client
        current_status_name = client.status_name
        if ('Sales_ActiveStatus_RequestCancellation' in disposition.name) and\
           ('Sales_ActiveStatus_RequestCancellationInitiated' in current_status_name):        

            user = self._req_user
            if client.account_manager:
                user = client.account_manager
            # create a team request
            contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                           status=ContractStatus.ACTIVE).first()
            if contract is None:
                raise ValueError("Active contract not found")    

            team_manager = None
            if user.team_member:
                team = user.team_member.team
                team_manager = team.manager
            else:
                team_manager = User.query.outerjoin(RACRole)\
                                         .filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
                
            if team_manager is None:
                raise ValueError("Team Manager not found")

            req_type = TeamRequestType.query.filter_by(code='REQUEST_CANCELLATION').first()
            if req_type is None:
                raise ValueError("Team Request Type not found")

            tr = TeamRequest(public_id=str(uuid.uuid4()),
                             requester_id=self._req_user.id,       
                             team_manager_id=team_manager.id,
                             request_type_id=req_type.id,
                             description=req_type.description,
                             contract_id=contract.id,
                             revision_id=None)
            db.session.add(tr)
            db.session.commit()
            TeamRequestChannel.send(team_manager.id,
                                    tr)
    def _audit_action(self, action):
        requestor = self._req_user
        # create audit record
        audit = Audit(public_id=str(uuid.uuid4()),
                      inserted_on=datetime.utcnow(),
                      auditable=Auditable.CLIENT.value,
                      auditable_subject_pubid=self._client.public_id,
                      action=action,
                      requestor_id=requestor.id,
                      message=action)

        db.session.add(audit)
        db.session.commit()


    def _on_deal_complete(self, params=None):
        client = self._client
        if 'Service_ActiveStatus_AcctManagerIntroComplete' in client.status_name:
            client.status_name = 'Sales_ActiveStatus_PendingFirstPayment'
            self._audit_action(ClientAction.DEAL_COMPLETE.value)
            db.session.commit()

    def _on_deal_reject(self, params=None):
        if 'Service_ActiveStatus_AcctManagerIntroComplete' in client.status_name:
            client.status_name = 'Sales_ActiveStatus_DealRejected'
            self._audit_action(ClientAction.DEAL_REJECT.value)
            db.session.commit()

    def on_execute_action(self, data):
        action = data.get('action')
        params = data.get('params')

        if not action:
            raise ValueError("Action not found")

        if action not in ClientAction.__members__:
            raise ValueError("Client action not supported")
        
        action_handler = "_on_{}".format(action.lower())
        func = getattr(self, action_handler, None) 
        if func:
            func(params)


# Client Tasks
class ClientTaskService(ClientService):
    _model = UserTask

    def __init__(self, id=None, public_id=None):
        super().__init__(id, public_id)

    def _queryset(self):
        return UserTask.query.filter_by(client_id=self._client.id).all()

# Client Team Requests
class ClientTrService(ClientService):
    _model = TeamRequest

    def __init__(self, id=None, public_id=None):
        super().__init__(id, public_id)

    def _queryset(self):
        return TeamRequest.query.outerjoin(DebtPaymentContract)\
                                .outerjoin(TeamRequestNote)\
                                .filter(DebtPaymentContract.client_id==self._client.id).all()

    
