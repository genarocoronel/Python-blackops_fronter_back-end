import enum
from app.main import db
from sqlalchemy import func
from sqlalchemy.orm import backref
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority 
from flask import current_app as app

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


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
    RECIEVE_SUMMON = 'recieve summon'
    ADD_COCLIENT = 'add coclient'

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
                            description= 'Call Client: {} Amendment approved'.format(action),
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
                credit_account = self.client.credit_report_account
                client = self.client
                for record in credit_account.records:
                    active_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=self.id,
                                                                                debt_id=record.id).first()
                    if active_debt:
                        record.push = True
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
                    db.session.commit()
                # new contract
                else:
                    self.status = ContractStatus.ACTIVE
                    db.session.commit()

                DebtPaymentSchedule.update_schedule(self, active_contract)

                


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
    transactions = db.relationship("DebtPaymentTransaction", backref="debt_payment_schedule") 

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
    def update_schedule(cls, new_contract, old_contract):
        term = new_contract.term 
        num_term_paid = old_contract.num_inst_completed

        if num_term_paid == 0:
            dps = cls.query.filter_by(contract_id=old_contract.id, 
                                      due_date=old_contract.payment_start_date)
            dps.contract_id = new_contract.id
            dps.amount = new_contract.monthly_fee
            db.session.commit()

        start = old_contract.payment_recurring_begin_date
        for i in range(1, num_term_paid):
            start = start + relativedelta(months=1)

        for i in range(0, (term - num_term_paid)):
            dps = cls.query.filter_by(contract_id=old_contract.id, 
                                      due_date=start).first()
            start = start + relativedelta(months=1)
            if dps is None:
                continue
            dps.contract_id = new_contract.id
            dps.amount = new_contract.monthly_fee
            db.session.commit()

        del_items = cls.query.filter(cls.due_date >= start).all()
        for item in del_items:
            db.session.delete(item)
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
