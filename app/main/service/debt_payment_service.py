from datetime import datetime
from app.main import db
from app.main.model.credit_report_account import CreditReportData, CreditPaymentPlan
from app.main.model.client import Client
from app.main.model.debt_payment import DebtPaymentSchedule, DebtEftStatus, DebtPaymentContract,\
                                         ContractStatus, DebtPaymentContractCreditData, ContractAction
from app.main.model.user import User
from app.main.model.rac import RACRole
from app.main.model.team import TeamRequestType, TeamRequest
from app.main.util.decorator import enforce_rac_required_roles
from app.main.core.rac import RACRoles
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, and_, desc, asc
import logging
import uuid

from flask import current_app as app

"""
Calculate contract values
"""
def calc_contract_vals(term, total_debt, co_sign=False): 

    cpp = CreditPaymentPlan.query.filter_by(name='Universal').first() 
    if cpp is None: 
        raise ValueError("Credit payment plan not present")

    new_term = term
    credit_monitoring_fee = cpp.monitoring_fee_1signer
    monthly_bank_fee = cpp.monthly_bank_fee
    min_allowed_fee = cpp.minimum_fee
    if co_sign is True:
        credit_monitoring_fee = cpp.monitoring_fee_2signer
    enrolled_debt = (total_debt * (cpp.enrolled_percent/100))
    total_fee = enrolled_debt + (credit_monitoring_fee * term) + (monthly_bank_fee * term)
    total_fee = round(total_fee, 2)
    if total_fee < min_allowed_fee:
        total_fee = min_allowed_fee
    # monthly fee
    monthly_fee = round((total_fee / term), 2)

    result = {
        "term": term,
        "total_debt" : total_debt,
        "enrolled_debt": enrolled_debt,
        "bank_fee": monthly_bank_fee,
        "min_fee": min_allowed_fee,
        "credit_monitoring_fee": credit_monitoring_fee,
        "monthly_fee": monthly_fee,
        "active": False,
    }

    return result

"""
Fetch PLANNED Contract for a given client
"""
@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def fetch_payment_contract(client):
    # check if client has co-client associated with it
    co_sign = False
    if client.client_id is not None:
        co_sign = True

    total_debt = 0

    # active contract
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                          status=ContractStatus.ACTIVE).first()
    if active_contract is not None:
        term = active_contract.term
        pymt_start = active_contract.payment_start_date
        pymt_rec_begin_date = active_contract.payment_recurring_begin_date

        result = {
            "term": term,
            "total_debt" : active_contract.total_debt,
            "enrolled_debt": active_contract.enrolled_debt,
            "bank_fee": 0,
            "min_fee": 0,
            "credit_monitoring_fee": 0,
            "monthly_fee": active_contract.monthly_fee,
            "active": True,
            "payment_1st_date": pymt_start.strftime('%m-%d-%Y'),
            "payment_2nd_date": pymt_rec_begin_date.strftime('%m-%d-%Y'),
        }

    else:
        term = 24
        pymt_start = datetime.utcnow()
        pymt_rec_begin_date = datetime.utcnow()

        # credit report
        credit_report = client.credit_report_account
        if credit_report is None:
            raise ValueError("Credit report for client not found")
        # credit records
        credit_records = credit_report.records
        if credit_records is None or len(credit_records) == 0:
            raise ValueError("Credit records are empty")
        # calculate the debt
        for record in credit_records:
            if record.push is True:
                total_debt = total_debt + float(record.balance_original)


        ## calcualte contract values
        result = calc_contract_vals(term, 
                                    total_debt, 
                                    co_sign) 

        result['payment_1st_date'] = pymt_start.strftime('%m-%d-%Y')
        result['payment_2nd_date'] = pymt_rec_begin_date.strftime('%m-%d-%Y')

    return result

"""
Update Payment contract for a given client
"""
@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def update_payment_contract(client, data):
    # add all pushed debt items to this contract
    credit_report = client.credit_report_account
    if credit_report is None:
        raise ValueError("Contract not valid: Credit report not found")
    # credit records
    credit_records = credit_report.records
    if credit_records is None or len(credit_records) == 0:
        raise ValueError("Contract not valid: No records in the credit report")

    # check if client has co-client associated with it
    co_sign = False
    if client.client_id is not None:
        co_sign = True

    term = data.get('term')
    total_debt = 0
    term = int(term)

    payment_1st_date = data.get('payment_1st_date') 
    payment_2nd_date = data.get('payment_2nd_date')

    pymt_start = datetime.strptime(payment_1st_date, '%m-%d-%Y')
    pymt_rec_begin_date = datetime.strptime(payment_2nd_date, '%m-%d-%Y')

    # planned contract 
    planned_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                           status=ContractStatus.PLANNED).first()
    if planned_contract is None:
        # create a payment contract
        planned_contract = DebtPaymentContract(client_id=client.id,
                                               term=term,
                                               current_action=ContractAction.NEW_CONTRACT,
                                               payment_start_date=pymt_start,
                                               payment_recurring_begin_date=pymt_rec_begin_date,
                                               inserted_on=datetime.now()) 
        db.session.add(planned_contract)
        db.session.commit()
    else:
        planned_contract.term = term
        planned_contract.payment_start_date = pymt_start
        planned_contract.payment_recurring_begin_date = pymt_rec_begin_date 

    # calculate the debt
    for record in credit_records:
        if record.push is True:
            total_debt = total_debt + float(record.balance_original) 
            enrolled = DebtPaymentContractCreditData.query.filter_by(contract_id=planned_contract.id, 
                                                                     debt_id=record.id).first()       
            if enrolled is None:
                enrolled = DebtPaymentContractCreditData(contract_id=planned_contract.id, 
                                                          debt_id=record.id,
                                                          creditor=record.creditor,
                                                          account_number=record.account_number,
                                                          balance_original=float(record.balance_original),
                                                         )
                db.session.add(enrolled)
                db.session.commit()
    
    ## calcualte contract values
    result = calc_contract_vals(term,
                                total_debt,
                                co_sign)

    planned_contract.total_debt = total_debt
    if planned_contract.enrolled_debt != result['enrolled_debt'] or planned_contract.monthly_fee != result['monthly_fee']:
        planned_contract.enrolled_debt = result['enrolled_debt']
        planned_contract.monthly_fee = result['monthly_fee']
        planned_contract.status = ContractStatus.PLANNED 
    
    # commit the changes
    db.session.commit()

    result['payment_1st_date'] = pymt_start.strftime('%m-%d-%Y')
    result['payment_2nd_date'] = pymt_rec_begin_date.strftime('%m-%d-%Y')
    return result


@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def payment_contract_action(client):
    # fetch the approved contract 
    # if not approve it
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.PLANNED).first()
    if contract is None:
        raise ValueError('Contract Not Found')
        
    contract.status = ContractStatus.APPROVED
    db.session.commit()
    action = contract.current_action

    ## fetch the action
    func = ''
    if action == ContractAction.NEW_CONTRACT:
        func = 'send_contract_for_signature'
        app.queue.enqueue('app.main.tasks.docusign.{}'.format(func), client.id)

    return "Success"
        

@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def fetch_plan_by_status(client, status):
    # contract
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status = status).first()
    if contract is None:
        raise ValueError("Requested plan not found")

    result = fetch_amendment_plan(client, contract.id)
    return result


@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def fetch_amendment_plan(client, plan_id=None):
    cpp = CreditPaymentPlan.query.filter_by(name='Universal').first()
    if cpp is None:
        raise ValueError("Payment Config not present")
    # active contract
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                          status=ContractStatus.ACTIVE).first()
    if active_contract is None:
        raise ValueError('Amendment plan failed: Active contract not found')

    if plan_id is not None:
        planned_contract = DebtPaymentContract.query.filter_by(id=plan_id).first()
    else:
        # planned contract
        planned_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                               status=ContractStatus.PLANNED).first()
    if planned_contract is None:
        raise ValueError('Amendment plan failed: Active contract not found')
    
    credit_monitoring_fee = cpp.monitoring_fee_1signer
    if client.co_client:
        credit_monitoring_fee = cpp.monitoring_fee_2signer
    bank_fee = cpp.monthly_bank_fee

    n_enrolled_debt = (planned_contract.total_debt * (cpp.enrolled_percent/100))
    n_total_fee   = n_enrolled_debt + (credit_monitoring_fee * planned_contract.term) + (bank_fee * planned_contract.term) 
    total_paid    = active_contract.total_paid
    n_monthly_fee = (n_total_fee - total_paid)/(planned_contract.term - active_contract.num_inst_completed)

    o_enrolled_debt = active_contract.enrolled_debt 
    o_total_fee = o_enrolled_debt + (credit_monitoring_fee * active_contract.term) + (bank_fee * active_contract.term)
    o_monthly_fee = active_contract.monthly_fee

    result = {
        'action': planned_contract.current_action.name,
        'new_term': planned_contract.term,
        'new_total_debt': planned_contract.total_debt,
        'new_enrolled_debt': n_enrolled_debt,
        'new_total_fee': n_total_fee,
        'new_monthly_fee': n_monthly_fee,
        'current_term': active_contract.term,
        'current_total_debt': active_contract.total_debt,
        'current_enrolled_debt': active_contract.enrolled_debt,
        'current_total_fee': o_total_fee,
        'current_monthly_fee': active_contract.monthly_fee, 
        'num_term_paid': active_contract.num_inst_completed,
        'total_paid': active_contract.total_paid,
        'service_fee': credit_monitoring_fee, #credit monitoring fee
        'bank_fee': bank_fee, 
    }
    return result

"""
Update debts in contract
"""
@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def update_amendment_plan(client, data):
    term = data.get('term')
    action = data.get('action') 
    enrolled_debts = data.get('debts')

    # add all pushed debt items to this contract
    credit_report = client.credit_report_account
    if credit_report is None:
        raise ValueError("Amendment update failed: Credit report not found")

    # check if client has co-client associated with it
    co_sign = False
    if client.client_id is not None:
        co_sign = True

    #if active contract exists
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                          status=ContractStatus.ACTIVE).first()

    if active_contract is None:
        raise ValueError('Active contract not present')
    # Not a term change
    if term is None:
        term = active_contract.term 

    pymt_start = active_contract.payment_start_date
    pymt_rec_begin_date = active_contract.payment_recurring_begin_date

    # if planned contract exists, reuse it 
    planned_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                           status=ContractStatus.PLANNED).first()
    if planned_contract is None:
        # create a payment contract
        planned_contract = DebtPaymentContract(client_id=client.id,
                                               term=term,
                                               current_action=action,
                                               payment_start_date=pymt_start,
                                               payment_recurring_begin_date=pymt_rec_begin_date,
                                               inserted_on=datetime.now()) 
        db.session.add(planned_contract)
        db.session.commit()
    else:
        planned_contract.term = term

    # add the debts 
    total_debt = planned_contract.total_debt
    if enrolled_debts is not None:
      total_debt = 0
      for item in enrolled_debts:
          debt_line = CreditReportData.query.filter_by(account_id=credit_report.id,
                                                       public_id=item['public_id']).first()
          if debt_line is None:
              raise ValueError('Not avalid debt line')

          # check if change in the balance, MODIFY DEBT 
          balance_original = debt_line.balance_original
          if debt_line.balance_original != balance_original:
              balance_original = item['balance_original'] 

          planned_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=planned_contract.id,
                                                                       debt_id=debt_line.id).first()                                      
          if planned_debt is None:
              planned_debt = DebtPaymentContractCreditData(contract_id=planned_contract.id,
                                                           debt_id=debt_line.id,
                                                           creditor=debt_line.creditor,                                                     
                                                           account_number=debt_line.account_number,
                                                           balance_original=float(balance_original),
                                                           )
              db.session.add(planned_debt)
              total_debt = total_debt + float(balance_original)

    planned_contract.total_debt = total_debt
    db.session.commit()

    result = fetch_amendment_plan(client) 
    planned_contract.enrolled_debt = result['new_enrolled_debt']
    planned_contract.monthly_fee = result['new_monthly_fee']
    # commit the changes
    db.session.commit()
    return result



@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def payment_contract_req4approve(user, client, data):
    action_title = data.get('action')
    action = ContractAction[action_title]
    requestor = user
    #team_manager = requestor.team_manager
     
    # update the payment contract
    update_amendment_plan(client, data)

    #  fetch the planned plan and change the status
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.PLANNED).first()
    if contract is None:
        raise ValueError("Saved plan not found")

    # fetch the request type based on the action
    req_type = TeamRequestType.query.filter(func.lower(TeamRequestType.title) == action.value).first()
    if req_type is None:
        raise ValueError("Request Type not found")

    svc_mgr = User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
    if svc_mgr is None:
        raise ValueError("Team Manager not found")

    ## create a Team Request
    team_request = TeamRequest(public_id=str(uuid.uuid4()),
                               requester_id=requestor.id,
                               team_manager_id=svc_mgr.id,
                               request_type_id=req_type.id,
                               description=req_type.description,
                               contract_id=contract.id)
    db.session.add(team_request)
                            
    ## send realtime notification to user
    #notification = Notification(user_id=team_manager.id,
    #                            type=NotificationType.USER,
    #                            title='New Team Request',
    #                            description='Team request for contact amendment')
     
    #TODO
    # send the notification on real time

    contract.agent_id = requestor.id
    contract.status = ContractStatus.REQ4APPROVAL
    contract.current_action = action
    db.session.commit()

    return {
        'success': True,
        'message': 'Approval request submitted'
    }

"""
Generate Debt Payment schedule for the client
Called after Document signature/s are completed.
"""
def create_debt_payment_schedule(contract):
    try:
        term = contract.term
        pymt_start = contract.payment_start_date
        monthly_fee = contract.monthly_fee
        dps = DebtPaymentSchedule(contract_id=contract.id,
                                  due_date=pymt_start,
                                  amount=monthly_fee,
                                  bank_fee=10)
        db.session.add(dps)
        db.session.commit()
        start = contract.payment_recurring_begin_date
        for i in range(1, term):
            dps = DebtPaymentSchedule(contract_id=contract.id,
                                      due_date=start,
                                      amount=monthly_fee,
                                      bank_fee=0)
            db.session.add(dps)
            db.session.commit()
            # add the schedule record
            start = start + relativedelta(months=1)
    except Exception as err:
        logging.warning("Create Debt Payment Schedule issue {}".format(str(err)))

def update_debt_payment_schedule(new_contract, old_contract):
    term = new_contract.term
    num_term_paid = old_contract.num_inst_completed
   
    if num_term_paid == 0:
        dps = DebtPaymentSchedule.query.filter_by(contract_id=old_contract.id, due_date=old_contract.payment_start_date)
        dps.contract_id = new_contract.id
        dps.amount = new_contract.monthly_fee
        db.session.commit()
        num_term_paid = 1

    # skip paid ones
    start = contract.payment_recurring_begin_date
    for i in range(1, num_term_paid): 
        start = start + relativedelta(months=1)
    
    for i in range(num_term_paid, term):
        dps = DebtPaymentSchedule.query.filter_by(contract_id=old_contract.id, due_date=start)
        dps.contract_id = new_contract.id
        dps.amount = new_contract.monthly_fee
        db.session.commit() 
        start = start + relativedelta(months=1)


def update_debt_payment_account(client, contract, active_contract):
    try:
        # check payment schedule is present or not
        pymt_schedule = contract.payment_schedule
        if pymt_schedule is None or len(pymt_schedule) == 0:
            # create payment schedule
            create_debt_payment_schedule(contract)
            # send to worker queue
            func = "register_customer"
            # app.queue.enqueue('app.main.tasks.debt_payment.{}'.format(func), client_id)
        else:
            if active_contract is None:
                raise ValueError("Active contract not found")

            update_debt_payment_schedule(contract, active_contract)

    except Exception as err:
        logging.warning("Create Payment account {}".format(str(err)))
        raise ValueError("Internal Error {}".format(str(err)))


def fetch_debt_payment_stats(client_id, start_date=None, end_date=None):
    result = []
    try: 
        client = Client.query.filter_by(public_id=client_id).first() 
        if start_date is not None:		
            dt_start = datetime.strptime(start_date, "%m/%d/%Y")
            if end_date is not None:
                dt_end = datetime.strptime(end_date, "%m/%d/%Y")
                records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.client_id==client.id,
                                                                DebtPaymentSchedule.due_date >= dt_start, 
                                                                DebtPaymentSchedule.due_date <= dt_end)).all()
            else:
                records = DebtPaymentSchedule.query.filter(and_(DebtPaymentSchedule.client_id==client.id, 
                                                                DebtPaymentSchedule.due_date >= dt_start)).all()
        else:
            records = client.debt_payment_schedule

        for record in records:
            item = {'due_date': record.due_date.strftime("%m/%d/%Y"), 
                    'amount': record.amount, 
                    'fee': record.bank_fee, 
                    'status': record.status.value}
            result.append(item)

    except Exception as err:
        raise ValueError("Internal Error")        
    
    return result


def fetch_payment_schedule(client):
    result = []

    # fetch the active contract
    active_contract = DebtPaymentContract.query.filter_by(status=ContractStatus.ACTIVE).first()
    if active_contract is None:
        raise ValueError('Active Payment Contract not fond')

    initial_contract = DebtPaymentContract.query.filter_by(status=ContractStatus.REPLACED)\
                                                .order_by(desc(DebtPaymentContract.inserted_on)).first()
    if initial_contract is None:
        initial_contract = active_contract

    total_fee = initial_contract.monthly_fee * initial_contract.term
    tmp = {
        'description': 'Invoice Amount',
        'type': 'Initial Balance',
        'status': '',
        'plus': total_fee,
        'minus': '',
        'balance': total_fee,
        'trans_date': '',
        'trans_id': '',
        'proj_date': '',
        'proj_amount': '',
        'proj_balance': total_fee,
        'commission': '',
        'earned_fee': '', 
    }
    result.append(tmp)

    records = DebtPaymentSchedule.query.outerjoin(DebtPaymentContract)\
                                       .filter(DebtPaymentContract.client_id==client.id)\
                                       .order_by(asc(DebtPaymentSchedule.due_date)).all()
    # error ?
    if len(records) == 0:
        raise ValueError('Payment Schecule not found')

    index = 0
    balance = total_fee
    current_contract = initial_contract
    for record in records:
        if current_contract != record.contract:
            # there is a change in contract 
            # create a change record 
            item = _get_contract_description(record.contract, current_contract, balance)
            result.append(item)
            balance = item['balance']
            current_contract = record.contract 

        index = index + 1
        balance = round(balance - record.amount, 2)
        status = 'Scheduled'
        if record.status == DebtEftStatus.Settled:
            status = 'Cleared'

        item = {
            'description': 'Payment {}'.format(index),
            'type': 'Payment',
            'status': status,
            'plus' : '',
            'minus': record.amount, 
            'balance': balance,
            'trans_date': '',
            'trans_id': '',
            'proj_date': record.due_date.strftime("%m/%d/%Y"),
            'proj_amount': record.amount,
            'proj_balance': balance,
            'commission': '',
            'earned_fee': '', 
        }
        result.append(item)


    return result

def _get_contract_description(new_contract, old_contract, balance):
    balance = round(balance, 2)
    new_balance = (new_contract.term - new_contract.num_inst_completed) * new_contract.monthly_fee
    new_balance = round(new_balance, 2)
    new_total_fee = new_contract.term * new_contract.monthly_fee
    
    type = ""
    status = ""
    minus = ""
    if new_contract.current_action == ContractAction.REMOVE_DEBTS:
        reduced = round(balance - new_balance, 2)
        desc = "Remove Debt"
        desc = desc + "New Term: \n".format(new_contract.term)
        desc = desc + "New Invoice Amount: ${}\n".format(new_total_fee)
        desc = desc + "Reduce Amount: ${}\n".format(reduced)

        type = "Remove Debt"
        status = "Approved"
        minus = reduced
        
    item = {
        'description': desc,
        'type': type,
        'status': status,
        'plus' : '',
        'minus': minus,
        'balance': new_balance,
        'trans_date': '',
        'trans_id': '',
        'proj_date': '',
        'proj_amount': '',
        'proj_balance': new_balance,
        'commission': '',
        'earned_fee': '',
    }

    return item
