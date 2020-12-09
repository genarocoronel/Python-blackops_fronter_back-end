from app.main import db
from app.main.model.debt_payment import DebtPaymentSchedule, DebtPaymentContractCreditData, DebtEftStatus, ContractStatus, RevisionStatus, ContractAction 
from app.main.model.credit_report_account import CreditReportAccount, CreditReportData
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority
from app.main.model.docproc import DocprocStatus
from app.main.model.client import ClientType, ProgramStatus
from app.main.model.sales_board import SalesFlow
from app.main.model.appointment import AppointmentStatus
from app.main.model.service_schedule import ServiceSchedule, ServiceScheduleStatus, ServiceScheduleType
from app.main.model.user import User
from app.main.model.rac import RACRole
from app.main.core.rac import RACRoles
from dateutil.relativedelta import relativedelta
from app.main.channels.notification import TaskChannel, ClientUpdateChannel
from app.main.tasks import channel as wkchannel
from sqlalchemy import desc, asc, and_
from datetime import datetime, timedelta
import app.main.tasks.docusign as docusign
import app.main.service.svc_schedule_service as svc_schedule_service

from flask import current_app as app

"""
Base Workflow class
"""
class Workflow(object):
    def __init__(self, obj, owner_id, client_id):
        self._object = obj 
        self._owner  = owner_id
        self._client_id = client_id
        self._status = obj.status
        
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    @property
    def owner(self):
        return self._owner

    ## task owner
    @owner.setter
    def owner(self, assigned_to):
        self._owner = assigned_to

    def save(self):
        if self._object.status != self._status:
            self._object.status = self._status
            db.session.commit()

    ## CREATE a USER TASK
    def _create_task(self, is_worker=False):
        due = datetime.utcnow() + timedelta(hours=self._task_due)  
        # if owner not present, assign to service manager
        if self.owner is None:
            svc_mgr = User.query.outerjoin(RACRole)\
                                .filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
            self.owner = svc_mgr.id
            
        agent_id = self.owner
        task = UserTask(assign_type=self._task_assign_type,
                        owner_id=agent_id,
                        priority=self._task_priority.name,
                        title=self._task_title,
                        description= self._task_desc,
                        due_date=due,
                        client_id=self._client_id,
                        object_type=self._task_ref_type,
                        object_id=self._object.id) 

        db.session.add(task)
        db.session.commit()
        # notify
        if is_worker is True:
            wkchannel.WkTaskChannel.send(agent_id,
                                         task)
        else:
            TaskChannel.send(agent_id,
                             task)

class GenericWorkflow(Workflow):
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_priority = TaskPriority.MEDIUM

    def __init__(self, client, obj_type, obj):
        assigned_to = client.account_manager_id
        client_id = client.id
        self._task_ref_type = obj_type         
        super().__init__(obj, assigned_to, client_id)

    def create_task(self, title, desc):
        self._task_title = title
        self._task_desc = desc
        self._create_task()
    
class AppointmentWorkflow(Workflow):
    _task_assign_type = TaskAssignType.AUTO
    _task_due = 24 ## task expiry in hours
    _task_priority = TaskPriority.MEDIUM
    _task_ref_type = 'Appointment'

    def __init__(self, appt):
        agent_id = appt.agent_id
        client_id = appt.client_id
        super().__init__(appt, agent_id, client_id)

    def _update_service_schedule(self, status):
        appt = self._object
        if appt.service_schedule:
            svc_schedule = appt.service_schedule
            svc_schedule.status = status
            svc_schedule.updated_on = datetime.utcnow()
            svc_schedule.updated_by_username = 'system'
            db.session.commit()

    def on_missed(self):
        self._task_title = 'Missed Appointment'
        self._task_desc = 'Missed Appointment - Action Required'

        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.MISSED.name
            self._update_service_schedule(ServiceScheduleStatus.INCOMPLETE.value)
            appt = self._object

            svc_mgr = User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
            if svc_mgr:
                self.owner = svc_mgr.id
                # TODO find the manager
                self._create_task()
                self.save()

    def on_incomplete(self, is_ss_triggered=False):
        self._task_title = 'Incomplete Appointment'
        self._task_desc = 'Appointment marked Incomplete - Action Required'

        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.INCOMPLETE.name
            if is_ss_triggered is False:
                self._update_service_schedule(ServiceScheduleStatus.INCOMPLETE.value)
            appt = self._object
            self.owner = appt.agent_id
            self._create_task()
            self.save()

    def on_completed(self, is_ss_triggered=False):
        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.COMPLETED.name
            if is_ss_triggered is False:
                self._update_service_schedule(ServiceScheduleStatus.COMPLETE.value)
            self.save()

            appt = self._object
            client = appt.client
            if appt.service_schedule:
                if ServiceScheduleType.INTRO_CALL.value in appt.service_schedule.type:
                    client.status = 'Acct Manager Intro Complete'
                    db.session.commit()
                    # send notififcaton
                    notice = wkchannel.ClientUpdateNotice(client, msg='Intro Call Completed')
                    ClientUpdateChannel.broadcast(notice)

                    app.queue.enqueue('app.main.tasks.mailer.send_intro_call',
                                      client.id, failure_ttl=300)
                    return

            if client.language == Language.SPANISH.name:
                app.queue.enqueue('app.main.tasks.mailer.send_spanish_general_call',  # task routine
                                  client.id, # client id
                                  failure_ttl=300)
            else:
                app.queue.enqueue('app.main.tasks.mailer.send_general_call_edms',  # task routine
                                  client.id, # client id
                                  failure_ttl=300)
    
    def on_ss_complete(self):
        self.on_completed(is_ss_triggered=True)

    def on_ss_incomplete(self):
        self.on_incomplete(is_ss_triggered=True)

class NSFWorkFlow(Workflow):
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_priority = TaskPriority.MEDIUM
    _task_ref_type = 'DebtPaymentContract'

    def __init__(self, client):
        client_id = client.id
        assigned_to = client.account_manager_id
        super().__init__(client, assigned_to, client_id)

    def on_failure(self):
        client = self._object
        client.status = 'Service Issue:NSF'

        self._task_title = 'Call Client'
        self._task_desc = 'Payment Failed.  Insufficient Funds in account.  Please call your client'
        # set all future payments non drafting
        self._create_task(is_worker=True)
        self.save()
        
        # send notififcaton
        notice = wkchannel.ClientUpdateNotice(client, msg='NSF Issue')
        wkchannel.WkCientUpdateChannel.broadcast(notice)

        # send mail
        app.queue.enqueue('app.main.tasks.mailer.send_nsf_draft_issue',
                           self._client_id, failure_ttl=300) 


# processing workflow
class DocprocWorkflow(Workflow):
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_priority = TaskPriority.MEDIUM
    _task_ref_type = 'Docproc'

    def __init__(self, docproc):
        assigned_to = docproc.docproc_user_id
        client_id = docproc.client_id
        super().__init__(docproc, assigned_to, client_id)

    def on_doc_recv(self):
        client = self._object.client
        if not client:
            # task can be created only for client docs
            return

        # already docproc in review
        if self.status == DocprocStatus.WAIT_AM_REVIEW.value:
            return

        self.status = DocprocStatus.WAIT_AM_REVIEW.value
        medium = self._object.source_channel
        self._task_title = 'New Message'
        self._task_desc = 'New {} Message from client'.format(medium)
        if client.account_manager:
            self.owner = client.account_manager_id
        else:
            svc_mgr = User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
            self.owner = svc_mgr.id

        self._create_task() 
        self.save()

        # send email confirmation
        app.queue.enqueue('app.main.tasks.mailer.send_new_document_notice',
                          client.id, 
                          self._object.id,
                          failure_ttl=300)

    def on_doc_update(self):
        self._task_title = 'Document Review'
        self._task_desc = 'Document Review - Action Required'
        docproc = self._object

        if self.status == DocprocStatus.NEW.value:
            client = docproc.client
            if not client:
                # task can be created only for client docs
                return

            self.status = DocprocStatus.WAIT_AM_REVIEW.value
            # Note that there are cases where Client is not yet set for a Doc
            if client.account_manager:
                self.owner = client.account_manager_id
            # assign to service manager
            else:
                svc_mgr = User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
                self.owner = svc_mgr.id
                
            self._create_task() 
            self.save()
            

    def on_task_declined(self, task):
        if self.status == DocprocStatus.WAIT_AM_REVIEW.value:
            self.status = DocprocStatus.REJECT.value 
            # notify doc processor 
            self.save()

    def on_task_completed(self, task):
        if self.status == DocprocStatus.WAIT_AM_REVIEW.value:
            self.status = DocprocStatus.APPROVED.value
            self.save()
   

## Debt Payment contract work flow   
class ContractWorkflow(Workflow):
    _rsign_worker_func = None
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_ref_type = 'DebtPaymentContract'
    _task_title = 'Call Client'
    _task_priority = TaskPriority.MEDIUM
    
    def __init__(self, contract):
        assigned_to = contract.agent_id
        client_id = contract.client_id
        super().__init__(contract, assigned_to, client_id)

    ## Client signed the contract
    def on_signed(self):
        self._task_title = 'Document for review'
        self._task_desc = 'Client signed, verify docusign document'
        if self.status == ContractStatus.APPROVED:          
            # download the signed document
            docusign.download_documents(self._object)                

            self.status = ContractStatus.SIGNED
            self._create_task(is_worker=True)
            self.save()

    """
    On Team Request approved
    """
    ## TEAM REQUEST APPROVED 
    def on_tr_approved(self, teamrequest):
        if self.status == ContractStatus.REQ4APPROVAL:
            self.status = ContractStatus.APPROVED
            ## task from webapp
            self._create_task()
            self.save()
            # send to worker queue for remote signature (docusign)
            if self._rsign_worker_func:
                app.queue.enqueue('app.main.tasks.docusign.{}'.format(self._rsign_worker_func), 
                                  self._client_id, failure_ttl=300)

    ## TEAM REQUEST DECLINED 
    def on_tr_declined(self, teamrequest):
        if self.status == ContractStatus.REQ4APPROVAL:
            self.status = ContractStatus.VOID
            ## task from webapp
            self._create_task()
            self.save()

    ## TASK completed
    def on_task_completed(self, task):
        if self.status == ContractStatus.SIGNED:
            # check for the document review task
            if 'document for review' in task.title.lower():
                client = self._object.client
                client_keys = [client.id, ]
                if client.co_client:
                    client_keys.append(client.co_client.id)
                debts = CreditReportData.query.outerjoin(CreditReportAccount)\
                                        .filter(CreditReportAccount.client_id.in_(client_keys)).all()
                for record in debts:
                    active_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=self._object.id,
                                                                                debt_id=record.id).first()
                    ## update push status
                    if active_debt:
                        record.push = True
                        ## update balance
                        if active_debt.balance_original != record.balance_original:
                            record.balance_original = active_debt.balance_original
                    else:
                        record.push = False
                db.session.commit()

                # change the current ACTIVE to REPLACED
                active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                                      status=ContractStatus.ACTIVE).first()
                if active_contract:
                    active_contract.status = ContractStatus.REPLACED
                    db.session.commit()
                    self._object.total_paid = active_contract.total_paid
                    self._object.num_inst_completed = active_contract.num_inst_completed
                    self._object.prev_id = active_contract.id
                    self.status = ContractStatus.ACTIVE
                    self.save()
                # new contract
                else:
                    self.status = ContractStatus.ACTIVE
                    self.save()

                # REMOVE DEBTS OR RECEIVE SUMMON
                contract = self._object
                if contract.current_action == ContractAction.REMOVE_DEBTS or \
                   contract.current_action == ContractAction.RECIEVE_SUMMON: 
                    # check 
                    if contract.monthly_fee <= 0:
                        client.status_name = 'Service_ActiveStatus_Fulfillment'
                        if client.credit_report_account.is_graduated() is True:
                            client.status_name = 'Service_ActiveStatus_Graduated'
                        
                count = 0
                for record in active_contract.payment_schedule:
                    count = count + 1
                    if count > self._object.term:
                        db.session.delete(record)
                        continue
                    # change the monthly fee for the EFTs not processed
                    if record.status == DebtEftStatus.FUTURE.name:
                        record.contract_id = self._object.id
                        record.amount = self._object.monthly_fee
                        if record.amount <= 0:
                            # will not be drafted
                            record.status = DebtEftStatus.PAUSED.name 

                db.session.commit()


            
## debt payment revision workflow
class RevisionWorkflow(Workflow):
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_ref_type = 'DebtPaymentRevision'
    _task_title = 'Call Client'
    _task_priority = TaskPriority.MEDIUM

    def __init__(self, revision):
        assigned_to = revision.agent_id 
        client_id = revision.contract.client_id
        super().__init__(revision, assigned_to, client_id)

    def on_tr_approved(self, teamrequest): 
        if self.status == RevisionStatus.OPENED:
            self.status = RevisionStatus.ACCEPTED
            ## task from webapp
            self._create_task()
            self.save()

    def on_tr_declined(self, teamrequest): 
        ## temperorary
        self._task_title = 'Call Client'
        self._task_desc = 'Request Rejected'

        if self.status == RevisionStatus.OPENED:
            self.status = RevisionStatus.REJECTED
            ## task from webapp
            self._create_task()
            self.save()
 
"""
factory method that returns the appropriate contract workflow
"""
def create_workflow(code, contract, revision=None):

    class NewContract(ContractWorkflow):
        def on_tr_approved(self, teamrequest):
            pass
        def on_tr_declined(self, teamrequest):
            pass
        ## called from task routine
        def on_signed(self):
            if self.status == ContractStatus.APPROVED:
                # create payment schedule
                DebtPaymentSchedule.create_schedule(self._object)
                self.status = ContractStatus.ACTIVE
                # transition lead to client
                client = self._object.client 
                client.type = ClientType.client
                self.save()
                # add epps customer
                # register client with EPPS provider
                app.queue.enqueue('app.main.tasks.debt_payment.register_customer',
                                  self._client_id, failure_ttl=300)
                ## send email  
                ## welcome letter
                app.queue.enqueue('app.main.tasks.mailer.send_welcome_letter',
                                  self._client_id, failure_ttl=300)
                ## privacy policy
                app.queue.enqueue('app.main.tasks.mailer.send_privacy_policy',
                                  self._client_id, failure_ttl=300)
                # download the signed document
                docusign.download_documents(self._object) 

                
                # Create initial service schedule for the client
                svc_schedule_service.create_svc_schedule(client)
                client.status = 'Assign to Acct Manager'
                client.program_status = ProgramStatus.SIGNED.name

                # update the sales board and sales flow
                if client.sales_rep:
                    sales_rep = client.sales_rep
                    sales_flow = SalesFlow.query.filter_by(agent_id=sales_rep.id,
                                                           lead_id=client.id).first()
                    if sales_flow:
                        sales_flow.ON_CONVERTED()

                    # Send a notification through worker channel
                    client.msg = "Client signed the contract."
                    wkchannel.WkClientNoticeChannel.send(sales_rep.id,
                                                         client)

                db.session.commit() 
                # send notififcaton
                notice = wkchannel.ClientUpdateNotice(client, msg='Client signed the contract', action='add')
                wkchannel.WkCientUpdateChannel.broadcast(notice)

              
    class TermChange(ContractWorkflow): 
        _rsign_worker_func = 'send_term_change_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New Contract Term Approved.\
                              Please call your client to complete docusign ammendment.'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'New Contract Term declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class AddDebts(ContractWorkflow):
        _rsign_worker_func = 'send_additional_debts_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New Debt added to contract Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'New Debt addition request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class RemoveDebts(ContractWorkflow):
        _rsign_worker_func = 'send_removal_debts_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Remove debt Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Remove Debt request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class ModifyDebts(ContractWorkflow):
        _rsign_worker_func = 'send_modify_debts_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Debt Modification Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Debt Modification request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class ReceiveSummon(ContractWorkflow):
        _rsign_worker_func = 'send_receive_summon_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Remove debt Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Receive Summon request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class NewEftAuth(ContractWorkflow):
        _rsign_worker_func = 'send_eft_authorization_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New EFT Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'New EFT Auth request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class AddCoClient(ContractWorkflow):
        _rsign_worker_func = 'send_add_coclient_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New Contract with Co-client Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Add Co-client request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class RemoveCoClient(ContractWorkflow):
        _rsign_worker_func = 'send_remove_coclient_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Remove Co-Client Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Remove Co-client request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)
    
    class ChangeDraftDate(RevisionWorkflow):

        def on_tr_approved(self, teamrequest):
            try:
                if self.status != RevisionStatus.OPENED:
                    return
                
                pymt_record = DebtPaymentSchedule.query\
                    .filter(and_(DebtPaymentSchedule.contract_id==self._object.contract_id,
                                 DebtPaymentSchedule.due_date > datetime.now())).order_by(asc(DebtPaymentSchedule.id)).first()
                if pymt_record:
                    new_due_date = self._object.fields['draft_date']
                    pymt_record.due_date = new_due_date # convert to datetime

                self._task_desc = 'Change Draft date Approved.\
                                   Please communicate with your client.' 
                super().on_tr_approved(teamrequest)
                # send change draft date notice to client

            except Exception as err:
                raise ValueError("ChangeDraftDate TR APPROVED handler issue")

    # Redraft for NSF  
    class NsfRedraft(RevisionWorkflow):
        def on_tr_approved(self, teamrequest):
            try:
                if self.status != RevisionStatus.OPENED:
                    return

                # fetch the last payment 
                pymt_record = DebtPaymentSchedule.query\
                                                 .filter(and_(DebtPaymentSchedule.contract_id==self._object.contract_id,
                                                              DebtPaymentSchedule.due_date < datetime.now())).order_by(desc(DebtPaymentSchedule.id)).first()
                if pymt_record.status == DebtEftStatus.NSF.name:
                    new_due_date = self._object.fields['draft_date']
                    pymt_record.due_date = new_due_date
                    # client status  
                    client = contract.client
                    if client.program_status == ProgramStatus.SIGNED.name:
                        client.status_name = 'Sales_ActiveStatus_PendingFirstPayment'
                    else:
                        client.status_name = 'Sales_ActiveStatus_Active' 

                    self._task_desc = 'NSF Redraft Approved.\
                                       Please communicate with your client.'
                    super().on_tr_approved(teamrequest)
                    # send notififcaton
                    notice = wkchannel.ClientUpdateNotice(client, msg='NSF Redraft request')
                    CientUpdateChannel.broadcast(notice)

            except Exception as err:
                raise ValueError("ChangeDraftDate TR APPROVED handler issue")
           

    class ChangeRecurDay(RevisionWorkflow):

        def on_tr_approved(self, teamrequest):
            try:
                if self.status != RevisionStatus.OPENED:
                    return
                
                day = int(self._object.fields['recur_day'])
                records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.contract_id==self._object.contract_id,
                                                                DebtPaymentSchedule.status==DebtEftStatus.FUTURE.name)).all()
                for record in records:
                    record.due_date = record.due_date.replace(day=day)
                self._task_desc = 'Change Draft date Approved.\
                                   Please communicate with your client.' 
                super().on_tr_approved(teamrequest)
            except Exception as err:
                raise ValueError("ChangeRecurDay ON TR APPROVED {}".format(str(err)))

    ## TODO CHECK SKIP PAYMENT LOGIC
    class SkipPayment(RevisionWorkflow):

        def on_tr_approved(self, teamrequest):
            try:
                if self._object.status != RevisionStatus.OPENED:
                    return

                # skip the next payment from the schedule
                pymt_record = DebtPaymentSchedule.query\
                                                 .filter(and_(DebtPaymentSchedule.contract_id==self._object.contract_id,
                                                              DebtPaymentSchedule.status==DebtEftStatus.FUTURE.name))\
                                                 .order_by(asc(DebtPaymentSchedule.id)).first()
                pymt_record.status = DebtEftStatus.SKIPPED.name
                self._task_desc = 'Skip Payment Approved.\
                                   Please communicate with your client.'
                super().on_tr_approved(teamrequest)

            except Exception as err:
                raise ValueError("SkipPayment ON TR APPROVED {}".format(str(err)))

    class Refund(RevisionWorkflow):

        def on_tr_approved(self, teamrequest):
            try:
                if self._object.status != RevisionStatus.OPENED:
                    return
                
                self._task_desc = 'Refund Request Approved.\
                                   Please communicate with your client.'
                super().on_tr_approved(teamrequest)

            except Exception as err:
                raise ValueError("SkipPayment ON TR APPROVED {}".format(str(err)))
    
    class RequestCancellation():

        def __init__(self, contract):
            self._contract = contract

        def on_tr_approved(self, teamrequest):
            client = self._contract.client
            program_status = client.program_status
            # before 1st Payment
            if program_status == ProgramStatus.SIGNED.name:
                client.status_name = 'Service_ActiveStatus_Cancelled_Before' 
                client.program_status = ProgramStatus.DROPPED.name
            # After 1st Payment
            elif program_status == ProgramStatus.ACTIVE.name:
                client.status_name = 'Service_ActiveStatus_Cancelled_After'
                client.program_status = ProgramStatus.CANCELLED.name

            # update the service schedule
            schedule = ServiceSchedule.query.filter_by(status=ServiceScheduleStatus.PENDING.value, 
                                                       client_id=client.id).all()
            for item in schedule:
                item.status = ServiceScheduleStatus.INCOMPLETE.value
            db.session.commit()
            # send notification
            notice = wkchannel.ClientUpdateNotice(client, msg='Request cancellation TR approved')
            CientUpdateChannel.broadcast(notice) 

            # create task
            wflow = GenericWorkflow(client, 'Client', client)
            wflow.create_task('Verify Smart Credit is Cancelled', 'Client cancelled from the program. Verify Smart Credit is cancelled.')

        # TBD
        def on_tr_declined(self, teamrequest):
            pass


    if 'NEW_CONTRACT' in code:
        return NewContract(contract)        
    elif 'ADD_DEBTS' in code:
        return AddDebts(contract)
    elif 'REMOVE_DEBTS' in code:
        return RemoveDebts(contract)
    elif 'MODIFY_DEBTS' in code:
        return ModifyDebts(contract)
    elif 'TERM_CHANGE' in code:
        return TermChange(contract)
    elif 'RECIEVE_SUMMON' in code:
        return ReceiveSummon(contract)
    elif 'ADD_COCLIENT' in code:
        return AddCoClient(contract)
    elif 'REMOVE_COCLIENT' in code:
        return RemoveCoClient(contract)
    elif 'NEW_EFT_AUTH' in code:
        return NewEftAuth(contract)
    elif 'CHANGE_DRAFT_DATE' in code:
        return ChangeDraftDate(revision)
    elif 'CHANGE_RECUR_DAY' in code:
        return ChangeRecurDay(revision)
    elif 'SKIP_PAYMENT' in code:
        return SkipPayment(revision)
    elif 'REFUND' in code:
        return Refund(revision)
    elif 'REQUEST_CANCELLATION' in code:
        return RequestCancellation(contract)
    elif 'NSF_REDRAFT' in code:
        return NsfRedraft(revision)
            
    # not supported action 
    return None 

from app.main.model.debt_payment import DebtPaymentContract, DebtPaymentContractRevision
from app.main.model.appointment import Appointment
from app.main.model.docproc import Docproc

def open_task_flow(task):

    if 'DebtPaymentContract' in task.object_type:
        obj = DebtPaymentContract.query.filter_by(id=task.object_id).first()
        if obj:
            return ContractWorkflow(obj)
    elif 'DebtPaymentRevision' in task.object_type:
        obj = DebtPaymentContractRevision.query.filter_by(id=task.object_id).first()
        if obj:
            return RevisionWorkflow(obj)
    elif 'Appointment' in task.object_type:
        obj = Appointment.query.filter_by(id=task.object_id).first()
        if obj:
            return AppointmentWorkflow(obj)
    elif 'Docproc' in task.object_type:
        obj = Docproc.query.filter_by(id=task.object_id).first()
        if obj:
            return DocprocWorkflow(obj)

    return None
