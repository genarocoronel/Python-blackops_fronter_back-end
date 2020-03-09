import enum
from app.main import db
from datetime import datetime
from sqlalchemy import func


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
    # relationship 
    client = db.relationship('Client', backref='payment_contracts')

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
    contract = db.relationship('DebtPaymentContract', backref='enrolled_debt_lines')
    debt = db.relationship('CreditReportData', backref='contract_enrolled_debts')

class DebtPaymentSchedule(db.Model):
    """ DB model for storing debt payment schedule and payment status."""   
    __tablename__ = "debt_payment_schedule"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # foreign key
    contract_id = db.Column(db.Integer, db.ForeignKey('debt_payment_contract.id', name='debt_payment_schedule_contract_id_fkey'))
    # relationship
    contract = db.relationship("DebtPaymentContract", backref="payment_schedule")

    due_date = db.Column(db.DateTime, nullable=False)
    amount  = db.Column(db.Float, nullable=False)
    bank_fee = db.Column(db.Float, nullable=True)
    status  = db.Column(db.Enum(DebtEftStatus), nullable=False, default=DebtEftStatus.Scheduled)

    # single EPPS transaction allowed, so One-to-One
    transactions = db.relationship("DebtPaymentTransaction", backref="debt_payment_schedule") 

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
