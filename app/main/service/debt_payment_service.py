from datetime import datetime
from app.main import db
from app.main.model.credit_report_account import CreditReportData, CreditPaymentPlan
from app.main.model.client import Client
from app.main.model.debt_payment import DebtPaymentSchedule, DebtEftStatus, DebtPaymentContract,\
                                         ContractStatus, DebtPaymentContractCreditData, ContractAction
from dateutil.relativedelta import relativedelta
from sqlalchemy import and_

import logging

from flask import current_app as app

"""
Calculate contract values
"""
def calc_contract_vals(term, total_debt, planned_debts_count, active_contract=None, co_sign=False): 

    new_term = term
    cpp = CreditPaymentPlan.query.filter_by(name='Universal').first() 
    if cpp is None: 
        raise ValueError("Credit payment plan not present")

    total_paid = 0
    num_inst_paid = 0
    active_debts_count = 0
    amend = False
    amend_reason = ""
    current_monthly_fee = 0
    current_enrolled_debt = 0
    if active_contract is not None:
        total_paid = active_contract.total_paid
        num_inst_paid = active_contract.num_inst_completed
        active_debts_count = len(active_contract.enrolled_debt_lines)
        current_monthly_fee = active_contract.monthly_fee
        current_enrolled_debt = active_contract.enrolled_debt

        # amend or not
        if planned_debts_count > active_debts_count:
            amend = True
            amend_reason = 'Debt Added'
        elif planned_debts_count < active_debts_count:
            amend = True
            amend_reason = 'Debt Removed'
        else:
            if active_contract.total_debt != total_debt:
                amend = True
                amend_reason = 'Debt Modified'
            elif active_contract.term != term:
                amend = True
                amend_reason = 'Term Change'

    enrolled_debt = (total_debt * (cpp.enrolled_percent/100))
    

    credit_monitoring_fee = cpp.monitoring_fee_1signer
    if co_sign is True:
        credit_monitoring_fee = cpp.monitoring_fee_2signer
    monthly_bank_fee = cpp.monthly_bank_fee
    min_allowed_fee = cpp.minimum_fee

    total_fee = enrolled_debt + (credit_monitoring_fee * new_term) + (monthly_bank_fee * new_term)
    total_fee = round(total_fee, 2)
    if total_fee < min_allowed_fee:
        total_fee = min_allowed_fee

    ## remaining to be paid 
    total_fee = total_fee - total_paid
    term = new_term - num_inst_paid
    # monthly fee
    monthly_fee = round((total_fee / term), 2)

    result = {
        "term": new_term,
        "num_term_paid": num_inst_paid,
        "enrolled_debt": enrolled_debt,
        "current_enrolled_debt": current_enrolled_debt,
        "total_paid": total_paid,
        "bank_fee": monthly_bank_fee,
        "min_fee": min_allowed_fee,
        "credit_monitoring_fee": credit_monitoring_fee,
        "current_monthly_fee": current_monthly_fee,
        "monthly_fee": monthly_fee,
        "amend": amend,
        "amend_reason": amend_reason,
    }

    return result

"""
Fetch PLANNED Contract for a given client
"""
def fetch_payment_contract(client):
    # check if client has co-client associated with it
    co_sign = False
    if client.client_id is not None:
        co_sign = True

    total_debt = 0
    planned_count = 0
    # check PLANNED contract exists or not
    pymt_plan = DebtPaymentContract.query.filter_by(client_id=client.id, 
                                                    status=ContractStatus.PLANNED).first()
    # payment contract (doesn't exist)
    if pymt_plan is not None:
        enrolled_debts = pymt_plan.enrolled_debt_lines
        planned_count  = len(enrolled_debts)
        if planned_count == 0:
            raise ValueError("No debts present for the contract")

        for record in enrolled_debts:
            total_debt = total_debt + float(record.balance_original)
    else:
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
                planned_count = planned_count + 1

    # active contract
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                          status=ContractStatus.ACTIVE).first()
    if pymt_plan is not None:
        term = pymt_plan.term
        pymt_start = pymt_plan.payment_start_date
        pymt_start = datetime.now() if pymt_start is None else pymt_start
        pymt_rec_begin_date = pymt_plan.payment_recurring_begin_date
        pymt_rec_begin_date = datetime.now() if pymt_rec_begin_date is None else pymt_rec_begin_date
    elif active_contract is not None:
        term = active_contract.term
        pymt_start = active_contract.payment_start_date
        pymt_rec_begin_date = active_contract.payment_recurring_begin_date
    else:
        term = 24
        pymt_start = datetime.utcnow()
        pymt_rec_begin_date = datetime.utcnow()

    ## calcualte contract values
    result = calc_contract_vals(term, 
                                total_debt, 
                                planned_count,
                                active_contract, 
                                co_sign) 

    result['payment_1st_date'] = pymt_start.strftime('%m-%d-%Y')
    result['payment_2nd_date'] = pymt_rec_begin_date.strftime('%m-%d-%Y')

    return result

def fetch_active_contract(client):
    # check ACTIVE contract exists or not
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                          status=ContractStatus.PLANNED).first()
    if active_contract is None:
        raise ValueError("valid contract not found")

    active_term = active_contract.term
    total_debt  = active_contract.total_debt
    enrolled_debt = active_contract.enrolled_debt
    monthly_fee = active_contract.monthly_fee
    total_paid = 0
    num_instalments = 0

    result = {
        'term': active_term,
        'total_debt': total_debt,
        'enrolled_debt': enrolled_debt,
        'monthly_fee': monthly_fee,
        'total_paid': total_paid,
        'num_paid_instalments': num_instalments,
    }

"""
Update Payment contract for a given client
"""
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
    term = int(term)
    #if active contract exists
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                          status=ContractStatus.ACTIVE).first()
    total_debt = 0
    planned_count = 0

    if active_contract is None:
        payment_1st_date = data.get('payment_1st_date') 
        payment_2nd_date = data.get('payment_2nd_date')

        pymt_start = datetime.strptime(payment_1st_date, '%m-%d-%Y')
        pymt_rec_begin_date = datetime.strptime(payment_2nd_date, '%m-%d-%Y')
    else:
        pymt_start = active_contract.payment_start_date
        pymt_rec_begin_date = active_contract.payment_recurring_begin_date

    # planned contract 
    planned_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                           status=ContractStatus.PLANNED).first()
    if planned_contract is None:
        # create a payment contract
        planned_contract = DebtPaymentContract(client_id=client.id,
                                               term=term,
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
            planned_count = planned_count + 1
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
                                planned_count,
                                active_contract,
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



def payment_contract_action(client):
    # fetch the approved contract 
    # if not approve it
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.APPROVED).first()
    if contract is None:
        approve_payment_contract(client)
        
    action = contract.current_action

    ## fetch the action
    func = ''
    if action == ContractAction.NEW_CONTRACT:
        func = 'send_contract_for_signature'
    else:
        active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                              status=ContractStatus.ACTIVE).first() 
        if active_contract is None:
            raise ValueError("Active contract not found")
        
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

    app.queue.enqueue('app.main.tasks.docusign.{}'.format(func), client.id)
    return "Success"
        
def fetch_plan_by_status(client, status):
    # contract
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status = status).first()
    if contract is None:
        raise ValueError("Requested plan not found")

    current_term = 0
    current_monthly_fee = 0
    current_enrolled_debt = 0
    total_paid = 0
    num_term_paid  = 0

    active = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                 status = ContractStatus.ACTIVE).first()  
    if active:
        current_term = active.term
        current_monthly_fee = active.monthly_fee
        current_enrolled_debt = active.enrolled_debt
        total_paid = active.total_paid
        num_term_paid = active.num_inst_completed 

    return {
        'action': contract.current_action.name, 
        'created_on': contract.inserted_on.strftime("%m/%d/%Y"),
        'term': contract.term,
        'current_term': current_term,
        'monthly_fee': contract.monthly_fee,
        'current_monthly_fee': current_monthly_fee,
        'enrolled_debt': contract.enrolled_debt,
        'current_enrolled_debt': current_enrolled_debt,
        'total_paid': total_paid,
        'num_term_paid': num_term_paid, 
    }
    
def fetch_debt_payment_plans(status):
    result = []

    # plans
    plans = DebtPaymentContract.query.filter_by(status=status).all()
    for plan in plans:
        tmp = {
            'action' : plan.current_action.name if plan.current_action else "",
            'client_id': plan.client.public_id,
            'first_name': plan.client.first_name,
            'last_name': plan.client.last_name,
            'created_on': plan.inserted_on.strftime("%m/%d/%Y"),
        }           
        result.append(tmp)

    return result

def payment_contract_req4approve(client, data):
    action = data.get('action')

    #  fetch the planned plan and change the status
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.PLANNED).first()
    if contract is None:
        raise ValueError("Saved plan not found")

    contract.status = ContractStatus.REQ4APPROVAL
    contract.current_action = action
    db.session.commit()

    ## send realtime notification to user
    ## goes here

    return {
        'success': True,
        'message': 'Approval request submitted'
    }

def payment_contract_approve(client):

    payment_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                           status=ContractStatus.REQ4APPROVAL).first()       
    if payment_contract is None:
        raise ValueError("Requested Contract Not found")

    # change the status to approved
    payment_contract.status = ContractStatus.APPROVED
    db.session.commit()

    ## check if we can send docusign document from here
    
    return {
        'success': True,
        'message': 'Plan approved'
    }

def payment_contract_activate(client):

    payment_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                           status=ContractStatus.SIGNED).first()
    if payment_contract is None:
        raise ValueError("Signed Contract Not found")

    # change the status to ACTIVE
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                          status=ContractStatus.ACTIVE).first()
    if active_contract:
        active_contract.status = ContractStatus.REPLACED
    payment_contract.status = ContractStatus.ACTIVE
    db.session.commit()

    # create an EPPS account, if not present
    update_debt_payment_account(client, payment_contract, active_contract)

    return {
        'success': True,
        'message': 'Plan activated'
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
