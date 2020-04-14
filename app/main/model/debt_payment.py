import enum
from app.main import db
from sqlalchemy import func
from sqlalchemy.orm import backref
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority 
from app.main.model.credit_report_account import CreditReportAccount, CreditReportData
from flask import current_app as app

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import desc, asc, and_
from app.main.core.errors import StateMachineError


class DebtEftStatus(enum.Enum):
    Scheduled = 'Scheduled'  # EFT Scheduled , Not forwarded to EPPS
    Processed = 'Processed'  # Processed, Sent to EPPS
    Settled   = 'Settled'    # EFT Transfer completed
    Failed    = 'Failed'     # EFT Payment failed

class ContractStatus(enum.Enum):
    PLANNED = 'planned'
    APPROVED = 'approved'      # contract sent to client
    REQ4APPROVAL = 'request approval'
    SIGNED   = 'signed'
    ACTIVE = 'active'          # Signed & Active 
    DECLINED = 'declined'      # client declined
    VOID     = 'void'          # service dept rejected
    REPLACED = 'replaced'      # replaced by active

class ContractAction(enum.Enum):
    NEW_CONTRACT = 'new contract'
    ADD_DEBTS = 'add debts'
    REMOVE_DEBTS = 'remove debts'
    MODIFY_DEBTS = 'modify debts'
    TERM_CHANGE = 'term change'
    RECIEVE_SUMMON = 'receive summon'
    ADD_COCLIENT = 'add coclient'
    REMOVE_COCLIENT = 'remove coclient'
    NEW_EFT_AUTH = 'new eft auth'

# Non docusign based amendment methods
class RevisionMethod(enum.Enum):
    SKIP_PAYMENT = 'skip payment'
    CHANGE_DRAFT_DATE = 'change draft date'
    CHANGE_RECUR_DAY = 'change draft day'
    MANUAL_ADJUSTMENT = 'manual adjustment'
    REFUND = 'refund'
    RE_INSTATE = 'reinstate',
    ADD_TO_EFT = 'add to eft',

class RevisionStatus(enum.Enum):
    OPENED = 'opened'
    ACCEPTED  = 'accepted'
    REJECTED  = 'rejected'
    
class DebtPaymentContract(db.Model):
    """ DB model for storing debt payment contract details """
    __tablename__ = "debt_payment_contract"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inserted_on = db.Column(db.DateTime, nullable=False)
    
    # contract date  
    sale_date = db.Column(db.DateTime, nullable=True)
    # payment term
    term = db.Column(db.Integer, nullable=True, default=24)
    payment_start_date = db.Column(db.DateTime, nullable=True)
    payment_recurring_begin_date = db.Column(db.DateTime, nullable=True)
 
    # debt
    total_debt = db.Column(db.Float, default=0)
    enrolled_debt = db.Column(db.Float, default=0)
    monthly_fee = db.Column(db.Float, default=0)
    # payment info
    total_paid = db.Column(db.Float, default=0)
    num_inst_completed = db.Column(db.Integer, default=0)
    # sales commission rate
    commission_rate = db.Column(db.Float, default=0.5)
    status  = db.Column(db.Enum(ContractStatus), default=ContractStatus.PLANNED)
    current_action  = db.Column(db.Enum(ContractAction), nullable=True)
    # foreign key
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='debt_payment_contract_client_id_fkey')) 
    # service agent id
    agent_id  = db.Column(db.Integer, db.ForeignKey('users.id', name='debt_payment_contract_agent_id_fkey'))
    # relationship 
    client = db.relationship('Client', backref='payment_contracts')
    agent = db.relationship('User', backref='payment_contracts')

    # previous contract
    prev_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id', name='debt_payment_contract_prev_id_fkey'))
    next_contract = db.relationship('DebtPaymentContract', uselist=False, remote_side=[prev_id]) 

    # STATE & EVENT HANDLERS
    def ON_SIGNED(self):
        # ACTIVE TO SIGNED
        if self.status == ContractStatus.APPROVED: 
            # check contract action
            # only amendments requires service person review 
            if self.current_action == ContractAction.NEW_CONTRACT:
                DebtPaymentSchedule.create_schedule(self)
                self.status = ContractStatus.ACTIVE
                db.session.commit()

                # register client with EPPS provider
                func = 'register_customer'
                app.queue.enqueue('app.main.tasks.debt_payment.{}'.format(func), self.client.id)

            else:
                # create a task if needed
                due = datetime.utcnow() + timedelta(hours=24)
                task = UserTask(assign_type=TaskAssignType.AUTO,
                                owner_id=self.agent_id,
                                priority=TaskPriority.MEDIUM,
                                title='Document for review',
                                description= 'Client signed, verify docusign document',
                                due_date=due,
                                client_id=self.client_id,
                                object_type='DebtPaymentContract',
                                object_id=self.id)
                self.status = ContractStatus.SIGNED
                db.session.add(task)
                db.session.commit() 

    # on Team Request completed action
    def ON_TR_APPROVED(self, req):
        # check the current status 
        if self.status == ContractStatus.REQ4APPROVAL:
            self.status = ContractStatus.APPROVED 
            db.session.commit()
            # send the amendment
            action = self.current_action
            if action == ContractAction.TERM_CHANGE:
                func = 'send_term_change_for_signature'
            elif action == ContractAction.ADD_DEBTS:
                func = 'send_additional_debts_for_signature'
            elif action == ContractAction.REMOVE_DEBTS:
                func = 'send_removal_debts_for_signature'
            elif action == ContractAction.MODIFY_DEBTS:
                func = 'send_modify_debts_for_signature'
            elif action == ContractAction.RECIEVE_SUMMON:
                func = 'send_receive_summon_for_signature'
            elif action == ContractAction.NEW_EFT_AUTH:
                func = 'send_eft_authorization_for_signature'
            elif action == ContractAction.ADD_COCLIENT:
                func = 'send_add_coclient_for_signature'
            elif action == ContractAction.REMOVE_COCLIENT:
                func = 'send_remove_coclient_for_signature'
            else:
                raise ValueError("Action not valid")
            
            # send the event to task queue
            app.queue.enqueue('app.main.tasks.docusign.{}'.format(func), self.client.id)

            # create a task if needed
            due = datetime.utcnow() + timedelta(hours=24)
            task = UserTask(assign_type=TaskAssignType.AUTO, 
                            owner_id=self.agent_id,
                            priority=TaskPriority.MEDIUM,
                            title='Call Client',
                            description= 'Call Client: {} Amendment approved'.format(action.name),
                            due_date=due, 
                            client_id=self.client_id,
                            object_type='DebtPaymentContract',
                            object_id=self.id)
            db.session.add(task)
            db.session.commit()


    def ON_TR_DECLINED(self, req):
        if self.status == ContractStatus.REQ4APPROVAL:
            self.status = ContractStatus.VOID 
            action = self.current_action.name if self.current_action else ''
            # create a task to the service user 
            due = datetime.utcnow() + timedelta(hours=24)
            task = UserTask(assign_type=TaskAssignType.AUTO,
                            owner_id=self.agent_id,
                            priority=TaskPriority.MEDIUM,
                            title='Call Client',
                            description= 'Call Client: {} Amendment rejected'.format(action),
                            due_date=due, 
                            client_id=this.client_id,
                            object_type='DebtPaymentContract',
                            object_id=this.id)

            db.session.add(task)
            db.session.commit() 

    def ON_TASK_COMPLETED(self, task):
        # SIGNED state
        if self.status == ContractStatus.SIGNED: 
            # check for the document review task
            if 'document for review' in task.title.lower():
                client = self.client
                client_keys = [client.id, ]
                if client.co_client:
                    client_keys.append(client.co_client.id)

                debts = CreditReportData.query.outerjoin(CreditReportAccount)\
                                              .filter(CreditReportAccount.client_id.in_(client_keys)).all()
                for record in debts:
                    active_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=self.id,
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
                    self.total_paid = active_contract.total_paid
                    self.num_inst_completed = active_contract.num_inst_completed 
                    self.status = ContractStatus.ACTIVE
                    self.prev_id = active_contract.id
                    db.session.commit()
                # new contract
                else:
                    self.status = ContractStatus.ACTIVE
                    db.session.commit()

                count = 0
                for record in active_contract.payment_schedule:
                    count = count + 1
                    if count > self.term:
                        db.session.delete(record)
                        continue

                    # change the monthly fee for the EFTs not processed
                    if record.status == DebtEftStatus.Scheduled:
                        record.contract_id = self.id 
                        record.amount = self.monthly_fee

                db.session.commit()
                


class DebtPaymentContractCreditData(db.Model):
    """ DB model for storing enrolled debts for a contract """
    __tablename__ = "debt_payment_contract_credit_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id', name='contract_credit_data_contract_id_fkey'))
    debt_id = db.Column(db.Integer, db.ForeignKey('credit_report_data.id', name='contract_credit_data_debt_id_fkey'))    

    # deep copy from credit report data
    creditor = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(25), nullable=False) 
    balance_original = db.Column(db.Float, default=0.0)

    # relationship
    contract = db.relationship('DebtPaymentContract', backref=backref('enrolled_debt_lines', cascade="all, delete-orphan"))
    debt = db.relationship('CreditReportData', backref=backref('contract_enrolled_debts', cascade="all, delete-orphan"))


class DebtPaymentSchedule(db.Model):
    """ DB model for storing debt payment schedule and payment status."""   
    __tablename__ = "debt_payment_schedule"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # foreign key
    contract_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id', name='debt_payment_schedule_contract_id_fkey'))
    # relationship
    contract = db.relationship("DebtPaymentContract", backref=backref('payment_schedule', cascade="all, delete-orphan"))

    due_date = db.Column(db.DateTime, nullable=False)
    amount  = db.Column(db.Float, nullable=False)
    bank_fee = db.Column(db.Float, nullable=True)
    status  = db.Column(db.Enum(DebtEftStatus), nullable=False, default=DebtEftStatus.Scheduled)

    # single EPPS transaction allowed, so One-to-One
    transaction = db.relationship("DebtPaymentTransaction", backref="debt_payment_schedule", uselist=False) 

    def ON_Processed(self):
        if self.status == DebtEftStatus.Scheduled:
            contract = self.contract
            if contract:
                contract.total_paid = contract.total_paid + self.amount
                contract.num_inst_completed = contract.num_inst_completed + 1
            self.status = DebtEftStatus.Processed
            db.session.commit()

    def ON_Settled(self):
        if self.status == DebtEftStatus.Scheduled:
            contract = self.contract
            if contract:
                contract.total_paid = contract.total_paid + self.amount
                contract.num_inst_completed = contract.num_inst_completed + 1
            self.status = DebtEftStatus.Settled
            db.session.commit()
        elif self.status == DebtEftStatus.Processed:
            self.status = DebtEftStatus.Settled
            db.session.commit()

    @classmethod
    def create_schedule(cls, contract):
        term = contract.term
        pymt_start = contract.payment_start_date
        monthly_fee = contract.monthly_fee
        obj = cls(contract_id=contract.id, 
                  due_date=pymt_start,
                  amount=monthly_fee,
                  bank_fee=10)
        db.session.add(obj)

        start = contract.payment_recurring_begin_date
        for i in range(1, term):
            obj = cls(contract_id=contract.id,        
                      due_date=start,
                      amount=monthly_fee,
                      bank_fee=10)
            db.session.add(obj)
            db.session.commit()
            start = start + relativedelta(months=1)

    @classmethod
    def update_next_payment_date(cls, contract, new_date):
        record = cls.query.filter(and_(cls.contract_id==contract.id, cls.due_date > datetime.now())).order_by(asc(cls.due_data)).first()
        record.due_date = due_date
        db.session.commit()

class DebtPaymentTransaction(db.Model):
    """ DB model for storing transaction details of debt payment record."""
    __tablename__ = "debt_payment_transaction"
  
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # EFT transaction
    trans_id = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(200), nullable=False)
    # status message
    message = db.Column(db.Text,  nullable=True)
    provider = db.Column(db.String(40), nullable=False, default="EPPS")

    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # payment schedule foriegn key 
    payment_id = db.Column(db.Integer, db.ForeignKey(DebtPaymentSchedule.id))


## Non debt based contract revisions
## Non Docusign related
class DebtPaymentContractRevision(db.Model):
    """ DB model for storing debt payment revision details """
    __tablename__ = "debt_payment_contract_revision"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # contract id
    contract_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id', name='debt_payment_revision_contarct_id_fkey'))
    # service agent id
    agent_id  = db.Column(db.Integer, db.ForeignKey('users.id', name='debt_payment_revision_agent_id_fkey'))
    # revision method/action 
    method  = db.Column(db.Enum(RevisionMethod), nullable=True) 
    status  = db.Column(db.Enum(RevisionStatus), default=RevisionStatus.OPENED)
    # revision fields
    fields = db.Column(db.JSON, default={})
    # relationship
    # contract to which revision is required
    contract = db.relationship('DebtPaymentContract', backref='revisions')
    agent = db.relationship('User', backref='payment_revisions') 

    def ON_TR_APPROVED(self, req):
        try:
            if self.status == RevisionStatus.OPENED:
                if self.method == RevisionMethod.CHANGE_DRAFT_DATE:
                    ## change the next draft date in the contract
                    ## update the schedule
                    pymt_record = DebtPaymentSchedule.query\
                        .filter(and_(DebtPaymentSchedule.contract_id==self.contract_id, 
                                     DebtPaymentSchedule.due_date > datetime.now())).order_by(asc(DebtPaymentSchedule.id)).first()
                    if pymt_record:
                        new_due_date = self.fields['draft_date'] 
                        pymt_record.due_date = new_due_date # convert to datetime

                elif self.method == RevisionMethod.CHANGE_RECUR_DAY:
                    # change the recurring day in the active contract
                    print(self.fields)
                    day = int(self.fields['recur_day'])
                    records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.contract_id==self.contract_id, 
                                                                    DebtPaymentSchedule.status==DebtEftStatus.Scheduled)).all()
                    for record in records:
                        record.due_date = record.due_date.replace(day=day)

                elif self.method == RevisionMethod.SKIP_PAYMENT: 
                    # skip the next payment from the schedule 
                    records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.contract_id==self.contract_id, 
                                                                    DebtPaymentSchedule.status==DebtEftStatus.Scheduled)).all()
                    for record in records:
                        due = record.due_date
                        record.due_date = due + relativedelta(months=1)

                elif self.method == RevisionMethod.REFUND:
                    pass

                self.status = RevisionStatus.ACCEPTED  
                # create a task if needed
                due = datetime.utcnow() + timedelta(hours=24)
                task = UserTask(assign_type=TaskAssignType.AUTO,
                                owner_id=self.agent_id,
                                priority=TaskPriority.MEDIUM,
                                title='Call Client',
                                description= 'Call Client: {} request approved'.format(self.method.value),
                                due_date=due,
                                client_id=self.contract.client_id,
                                object_type='DebtPaymentRevision',
                                object_id=self.id)
                db.session.add(task)
                db.session.commit()
        except Exception as err:
            print("SM Error {}".format(str(err))) 
            raise StateMachineError("Contract revision SM error {}".format(str(err)))
