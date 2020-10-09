import enum
from app.main import db
from sqlalchemy import func
from sqlalchemy.orm import backref
from app.main.model.credit_report_account import CreditReportAccount, CreditReportData
from flask import current_app as app

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import desc, asc, and_
from app.main.core.errors import StateMachineError
from app.main.channels.notification import TaskChannel
from app.main.model.sales_board import SalesCommission
import inflect

class DebtEftStatus(enum.Enum):
    FUTURE = 'Future'  # EFT Scheduled , Not forwarded to EPPS
    SEND_TO_EFT = 'Send to EFT'  # Processed, Sent to EPPS
    TRANSMITTED = 'Transmitted'
    CLEARED   = 'Cleared'    # EFT Transfer completed
    NSF    = 'NSF'     # EFT Payment failed
    SKIPPED = 'Skipped' # payment skipped
    PAUSED = 'Paused' # payment paused (not to draft)

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
    RE_INSTATE = 'reinstate'
    ADD_TO_EFT = 'add to eft'
    NSF_REDRAFT = 'nsf redraft' # NSF redraft

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
    # credit monitoring fee & bank fee
    credit_monitoring_fee = db.Column(db.Float, default=0)
    bank_fee = db.Column(db.Float, default=0)
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
    client = db.relationship('Client', backref=backref('payment_contracts', lazy='dynamic', cascade="all, delete-orphan"))
    agent = db.relationship('User', backref=backref('payment_contracts', lazy='dynamic'))
    # previous contract
    prev_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id', name='debt_payment_contract_prev_id_fkey'))
    next_contract = db.relationship('DebtPaymentContract', uselist=False, remote_side=[prev_id]) 


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
    status  = db.Column(db.String(24), nullable=False, default=DebtEftStatus.FUTURE.name)
    # description
    desc = db.Column(db.String(100), nullable=True)

    # single EPPS transaction allowed, so One-to-One
    transaction = db.relationship("DebtPaymentTransaction", backref="debt_payment_schedule", uselist=False) 

    def on_eft_transmitted(self):
        if self.status == DebtEftStatus.SEND_TO_EFT.name:
            self.status = DebtEftStatus.TRANSMITTED.name
            db.session.commit()    

    def on_eft_failed(self):
        if self.status == DebtEftStatus.SEND_TO_EFT.name or\
           self.status == DebtEftStatus.TRANSMITTED.name:
            self.status = DebtEftStatus.NSF.name
            db.session.commit()

    def on_eft_settled(self):
        if self.status == DebtEftStatus.SEND_TO_EFT.name or\
           self.status == DebtEftStatus.TRANSMITTED.name:
            contract = self.contract
            if contract:
                contract.total_paid = contract.total_paid + self.amount
                contract.num_inst_completed = contract.num_inst_completed + 1
                # check the installments
                if contract.num_inst_completed == 1 or contract.num_inst_completed == 2:
                    client = contract.client
                    amount = round( contract.total_debt * (contract.commission_rate / 100), 2)
                    desc = 'Commission from 1st Payment'
                    if contract.num_inst_completed == 2:
                        desc = 'Commission from 2nd Payment'
                    sc = SalesCommision(agent_id=client.sales_rep_id,
                                        client_id=client.id,
                                        transaction_id=self.transaction.id,
                                        amount=amount,
                                        description=desc,
                                        created_date=datetime.utcnow())
                    db.session.add(sc)

            self.status = DebtEftStatus.CLEARED.name
            db.session.commit()

    @classmethod
    def create_schedule(cls, contract):
        p = inflect.engine() 
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
            desc = "{} Payment".format(p.ordinal(i))
            obj = cls(contract_id=contract.id,        
                      due_date=start,
                      amount=monthly_fee,
                      bank_fee=10,
                      desc=desc)
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
    # sales commission
    commission = db.relationship("SalesCommission", backref="payment_transaction", uselist=False) 


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


class EftReturnFee(db.Model):
    """ DB model for storing EFT Return fee information """
    __tablename__ = "eft_return_fee"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    code = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, default=0)
    created_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, default=datetime.utcnow)

    # added/modified by 
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id', name='eft_return_fee_agent_id_fkey'))
    agent = db.relationship('User', backref=backref('eft_return_fee_records', lazy='dynamic')) 

