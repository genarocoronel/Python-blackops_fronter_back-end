from flask import current_app as app
from app.main import db
from app.main.model.debt_payment import DebtPaymentSchedule, DebtPaymentContractCreditData, DebtEftStatus, ContractStatus, RevisionStatus 
from app.main.model.credit_report_account import CreditReportAccount, CreditReportData
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority
from app.main.model.docproc import DocprocStatus
from dateutil.relativedelta import relativedelta
from app.main.channels.notification import TaskChannel
from sqlalchemy import desc, asc, and_
from datetime import datetime, timedelta
from app.main.tasks import debt_payment as pymt_tasks
from app.main.tasks.mailer import send_welcome_letter, send_spanish_welcome_letter, send_privacy_policy
from app.main.tasks import docusign

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
    def _create_task(self):
        due = datetime.utcnow() + timedelta(hours=self._task_due)  
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
    

## Doc processing workflow
class DocprocWorkflow(Workflow):
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_priority = TaskPriority.MEDIUM
    _task_ref_type = 'Docproc'

    def __init__(self, docproc):
        assigned_to = docproc.docproc_user_id
        client_id = docproc.client_id
        super().__init__(docproc, assigned_to, client_id)

    def on_doc_update(self):
        self._task_title = 'Document Review'
        self._task_desc = 'Document Review - Action Required'
        if self.status == DocprocStatus.NEW.value:
            self.status = DocprocStatus.WAIT_AM_REVIEW.value
            client = self._object.client
            self.owner = client.account_manager_id
            self._create_task() 
            self.save()

    def on_task_declined(self):
        if self.status == DocprocStatus.WAIT_AM_REVIEW.value:
            self.status = DocprocStatus.REJECT.value 
            # notify doc processor 

    def on_task_completed(self):
        if self.status == DocprocStatus.WAIT_AM_REVIEW.value:
            self.status = DocprocStatus.APPROVED.value
   

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
            self.status = ContractStatus.SIGNED
            self._create_task()
            self.save()

    """
    On Team Request approved
    """
    ## TEAM REQUEST APPROVED 
    def on_tr_approved(self, teamrequest):
        if self.status == ContractStatus.REQ4APPROVAL:
            self.status = ContractStatus.APPROVED
            self._create_task()
            self.save()
            # send to worker queue for remote signature (docusign)
            if self._rsign_worker_func:
                app.queue.enqueue('app.main.tasks.docusign.{}'.format(self._rsign_worker_func), 
                                  self._client_id)

    ## TEAM REQUEST DECLINED 
    def on_tr_declined(self, teamrequest):
        if self.status == ContractStatus.REQ4APPROVAL:
            self.status = ContractStatus.VOID
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

                count = 0
                for record in active_contract.payment_schedule:
                    count = count + 1
                    if count > self._object.term:
                        db.session.delete(record)
                        continue

                    # change the monthly fee for the EFTs not processed
                    if record.status == DebtEftStatus.Scheduled:
                        record.contract_id = self._object.id
                        record.amount = self._object.monthly_fee

                db.session.commit()

                # download the signed document
                docusign.download_documents(self._object)                

            
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
            self._create_task()
            self.save()

    def on_tr_declined(self, teamrequest): 
        ## temperorary
        self._task_title = 'Call Client'
        self._task_desc = 'Request Rejected'

        if self.status == RevisionStatus.OPENED:
            self.status = RevisionStatus.REJECTED
            self._create_task()
            self.save()
 
"""
factory method that returns the appropriate contract workflow
"""
def open_contract_flow(code, contract, revision=None):

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
                self.save()
                # add epps customer
                # register client with EPPS provider
                pymt_tasks.register_customer(self._client_id)
                ## send email  
                ## welcome letter
                send_welcome_letter(self._client_id)
                ## privacy policy
                send_privacy_policy(self._client_id)
                # download the signed document
                docusign.download_documents(self._object) 
              
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

    class ChangeRecurDay(RevisionWorkflow):

        def on_tr_approved(self, teamrequest):
            try:
                if self.status != RevisionStatus.OPENED:
                    return
                
                day = int(self._object.fields['recur_day'])
                records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.contract_id==self._object.contract_id,
                                                                DebtPaymentSchedule.status==DebtEftStatus.Scheduled)).all()
                for record in records:
                    record.due_date = record.due_date.replace(day=day)
                self._task_desc = 'Change Draft date Approved.\
                                   Please communicate with your client.' 
                super().on_tr_approved(teamrequest)
            except Exception as err:
                raise ValueError("ChangeRecurDay ON TR APPROVED {}".format(str(err)))

    class SkipPayment(RevisionWorkflow):

        def on_tr_approved(self, teamrequest):
            try:
                if self._object.status != RevisionStatus.OPENED:
                    return

                # skip the next payment from the schedule
                records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.contract_id==self._object.contract_id,
                                                                DebtPaymentSchedule.status==DebtEftStatus.Scheduled)).all()
                for record in records:
                    due = record.due_date
                    record.due_date = due + relativedelta(months=1)

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
