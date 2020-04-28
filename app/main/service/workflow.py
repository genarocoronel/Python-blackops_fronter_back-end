from flask import current_app as app
from app.main import db
from app.main.model.debt_payment import DebtPaymentSchedule, DebtEftStatus, ContractStatus, RevisionStatus 
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority
from dateutil.relativedelta import relativedelta
from app.main.channels.notification import TaskChannel
from sqlalchemy import desc, asc, and_
from datetime import datetime, timedelta

"""
Base Workflow class
"""
class Workflow(object):
    def __init__(self, client):
        self._client = client

    def _create_task(self):
        due = datetime.utcnow() + timedelta(hours=self._task_due)  
        task = UserTask(assign_type=self._task_assign_type,
                        owner_id=self._owner_id,
                        priority=self._task_priority,
                        title=self._task_title,
                        description= self._task_desc,
                        due_date=due,
                        client_id=self._client.id,
                        object_type=self._task_ref_type,
                        object_id=self._task_obj.id) 

        db.session.add(task)
        db.session.commit()
        # notify
        TaskChannel.send(self._owner_id,
                         task)

## Debt Payment contract work flow   
class ContractWorkFlow(Workflow):
    _rsign_worker_func = None
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_ref_type = 'DebtPaymentContract'
    _task_title = 'Call Client'
    _task_priority = TaskPriority.MEDIUM
    
    def __init__(self, contract):
        self._contract = contract 
        super().__init__(contract.client)
      
    ## Client signed the contract
    def on_signed(self):
        self._task_title = 'Document for review'
        self._task_desc = 'Client signed, verify docusign document'
        if self._contract and self._contract.status == ContractStatus.APPROVED:          
            self._owner_id = self._contract.agent_id
            self._task_obj = self._contract
            self._create_task()
            self._contract.status = ContractStatus.SIGNED
            db.session.commit()

    """
    On Team Request approved
    """
    def on_tr_approved(self, teamrequest):
        if self._contract.status == ContractStatus.REQ4APPROVAL:
            self._contract.status = ContractStatus.APPROVED
            db.session.commit()
            # send to worker queue for remote signature (docusign)
            if self._rsign_worker_func:
                app.queue.enqueue('app.main.tasks.docusign.{}'.format(self._rsign_worker_func), 
                                  self._client.id)

            self._owner_id = self._contract.agent_id
            self._task_obj = self._contract
            self._create_task()

    
    def on_tr_declined(self, teamrequest):
        if self._contract.status == ContractStatus.REQ4APPROVAL:
            self._contract.status = ContractStatus.VOID
            due = datetime.utcnow() + timedelta(hours=self._task_due)
            
            self._owner_id = self._contract.agent_id
            self._task_obj = self._contract
            self._create_task()

            
## debt payment revision workflow
class RevisionWorkFlow(Workflow):
    _task_due = 24 ## task expiry in hours
    _task_assign_type = TaskAssignType.AUTO
    _task_ref_type = 'DebtPaymentRevision'
    _task_title = 'Call Client'
    _task_priority = TaskPriority.MEDIUM

    def __init__(self, revision):
        self._revision = revision
        client = revision.contract.client
        super().__init__(client)

    def on_tr_approved(self, teamrequest): 
        if self._revision.status == RevisionStatus.OPENED:
            self._revision.status = RevisionStatus.ACCEPTED
            db.session.commit()

            self._owner_id = self._revision.agent_id
            self._task_obj = self._revision
            self._create_task()

    def on_tr_declined(self, teamrequest): 
        ## temperorary
        self._task_title = 'Call Client'
        self._task_desc = 'Request Rejected'

        if self._revision.status == RevisionStatus.OPENED:
            self._revision.status = RevisionStatus.REJECTED
            db.session.commit()

            self._owner_id = self._revision.agent_id
            self._task_obj = self._revision
            self._create_task()
 
"""
factory method that returns the appropriate contract workflow
"""
def open_contract_flow(code, contract, revision=None):

    class NewContract(ContractWorkFlow):
        def on_tr_approved(self, teamrequest):
            pass
        def on_tr_declined(self, teamrequest):
            pass
        def on_signed(self):
            if self._contract and self._contract.status == ContractStatus.APPROVED:
                # create payment schedule
                DebtPaymentSchedule.create_schedule(self._contract)
                self._contract.status = ContractStatus.ACTIVE
                db.session.commit()
                # add epps customer
                # register client with EPPS provider
                func = 'register_customer'
                app.queue.enqueue('app.main.tasks.debt_payment.{}'.format(func), self._client.id)

    class TermChange(ContractWorkFlow): 
        _rsign_worker_func = 'send_term_change_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New Contract Term Approved.\
                              Please call your client to complete docusign ammendment.'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'New Contract Term declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class AddDebts(ContractWorkFlow):
        _rsign_worker_func = 'send_additional_debts_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New Debt added to contract Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'New Debt addition request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class RemoveDebts(ContractWorkFlow):
        _rsign_worker_func = 'send_removal_debts_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Remove debt Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Remove Debt request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class ModifyDebts(ContractWorkFlow):
        _rsign_worker_func = 'send_modify_debts_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Debt Modification Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Debt Modification request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class ReceiveSummon(ContractWorkFlow):
        _rsign_worker_func = 'send_receive_summon_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Remove debt Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Receive Summon request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class NewEftAuth(ContractWorkFlow):
        _rsign_worker_func = 'send_eft_authorization_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New EFT Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'New EFT Auth request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class AddCoClient(ContractWorkFlow):
        _rsign_worker_func = 'send_add_coclient_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'New Contract with Co-client Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Add Co-client request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    class RemoveCoClient(ContractWorkFlow):
        _rsign_worker_func = 'send_remove_coclient_for_signature'

        def on_tr_approved(self, teamrequest):
            self._task_desc = 'Remove Co-Client Approved.\
                               Please call your client to complete docusign ammendment'
            super().on_tr_approved(teamrequest)

        def on_tr_declined(self, teamrequest):
            self._task_desc = 'Remove Co-client request declined.\
                               Please communicate to your client.'
            super().on_tr_declined(teamrequest)

    
    class ChangeDraftDate(RevisionWorkFlow):

        def on_tr_approved(self, teamrequest):
            try:
                if self._revision.status != RevisionStatus.OPENED:
                    return
                
                pymt_record = DebtPaymentSchedule.query\
                    .filter(and_(DebtPaymentSchedule.contract_id==self._revision.contract_id,
                                 DebtPaymentSchedule.due_date > datetime.now())).order_by(asc(DebtPaymentSchedule.id)).first()
                if pymt_record:
                    new_due_date = self._revision.fields['draft_date']
                    pymt_record.due_date = new_due_date # convert to datetime

                self._task_desc = 'Change Draft date Approved.\
                                   Please communicate with your client.' 
                super().on_tr_approved(teamrequest)
            except Exception as err:
                raise ValueError("ChangeDraftDate TR APPROVED handler issue")

    class ChangeRecurDay(RevisionWorkFlow):

        def on_tr_approved(self, teamrequest):
            try:
                if self._revision.status != RevisionStatus.OPENED:
                    return
                

                day = int(self._revision.fields['recur_day'])
                records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.contract_id==self._revision.contract_id,
                                                                DebtPaymentSchedule.status==DebtEftStatus.Scheduled)).all()
                for record in records:
                    record.due_date = record.due_date.replace(day=day)
                self._task_desc = 'Change Draft date Approved.\
                                   Please communicate with your client.' 
                super().on_tr_approved(teamrequest)
            except Exception as err:
                raise ValueError("ChangeRecurDay ON TR APPROVED {}".format(str(err)))

    class SkipPayment(RevisionWorkFlow):

        def on_tr_approved(self, teamrequest):
            try:
                if self._revision.status != RevisionStatus.OPENED:
                    return

                # skip the next payment from the schedule
                records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.contract_id==self._revision.contract_id,
                                                                DebtPaymentSchedule.status==DebtEftStatus.Scheduled)).all()
                for record in records:
                    due = record.due_date
                    record.due_date = due + relativedelta(months=1)

                self._task_desc = 'Skip Payment Approved.\
                                   Please communicate with your client.'
                super().on_tr_approved(teamrequest)

            except Exception as err:
                raise ValueError("SkipPayment ON TR APPROVED {}".format(str(err)))

    class Refund(RevisionWorkFlow):

        def on_tr_approved(self, teamrequest):
            try:
                if self._revision.status != RevisionStatus.OPENED:
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
