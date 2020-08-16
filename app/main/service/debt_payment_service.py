from datetime import datetime
from app.main import db
from app.main.model.credit_report_account import CreditReportData, CreditPaymentPlan
from app.main.model.client import Client
from app.main.model.debt_payment import DebtPaymentSchedule, DebtEftStatus, DebtPaymentContract, ContractStatus, \
                                        DebtPaymentContractCreditData, ContractAction, DebtPaymentContractRevision, \
                                        RevisionMethod, RevisionStatus
from app.main.model.user import User
from app.main.model.rac import RACRole
from app.main.model.team import TeamRequestType, TeamRequest
from app.main.util.decorator import enforce_rac_required_roles
from app.main.core.rac import RACRoles
from app.main.service.client_service import fetch_client_combined_debts
from app.main.service.teamrequest_service import create_team_request
from app.main.channels.notification import TeamRequestChannel
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, and_, desc, asc, or_
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
        "total_paid": 0,
        "num_term_paid": 0,
        "active": False,
    }

    return result

"""
Fetch PLANNED Contract for a given client
"""
def fetch_payment_contract(client):
    # check if client has co-client associated with it
    co_sign = False
    if client.co_client:
        co_sign = True

    total_debt = 0

    is_active = True
    # active contract
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.ACTIVE).first()
    if not contract: 
        is_active = False
        # fetch the latest contract 
        contract = DebtPaymentContract.query.filter(and_(DebtPaymentContract.client_id==client.id, DebtPaymentContract.status!=ContractStatus.REPLACED))\
                                      .order_by(desc(DebtPaymentContract.id)).first()
    if contract:
        term = contract.term
        pymt_start = contract.payment_start_date
        pymt_rec_begin_date = contract.payment_recurring_begin_date

        result = {
            "term": term,
            "total_debt" : contract.total_debt,
            "enrolled_debt": contract.enrolled_debt,
            "bank_fee": contract.bank_fee,
            "min_fee": 0,
            "credit_monitoring_fee": contract.credit_monitoring_fee,
            "monthly_fee": contract.monthly_fee,
            "total_paid": contract.total_paid,
            "num_term_paid": contract.num_inst_completed,
            "active": is_active,
            "payment_1st_date": pymt_start.strftime('%m-%d-%Y'),
            "payment_2nd_date": pymt_rec_begin_date.strftime('%m-%d-%Y'),
        }

    else:
        term = 24
        pymt_start = datetime.utcnow()
        pymt_rec_begin_date = datetime.utcnow()

        combined_debts = fetch_client_combined_debts(client)
        if len(combined_debts) == 0:
            result = {
              "term": 24,
              "total_debt": 0,
              "enrolled_debt": 0,
              "bank_fee": 20,
              "min_fee": 0,
              "credit_monitoring_fee": 59,
              "monthly_fee": 0, 
              "total_paid": 0,
              "num_term_paid": 0,
              "active": False, 
              "payment_1st_date": datetime.utcnow().strftime('%m-%d-%Y'),
              "payment_2nd_date": datetime.utcnow().strftime('%m-%d-%Y'),
            }
            return result

        # calculate the debt
        for record in combined_debts:
            if record.push is True:
                total_debt = total_debt + float(record.balance_original)


        ## calcualte contract values
        result = calc_contract_vals(term, 
                                    total_debt, 
                                    co_sign) 

        result['payment_1st_date'] = pymt_start.strftime('%m-%d-%Y')
        result['payment_2nd_date'] = pymt_rec_begin_date.strftime('%m-%d-%Y')

    return result

def fetch_active_contract(client):
   
    # active contract
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.ACTIVE).first()
    if not contract:
        result = {
            "term": 24,
            "total_debt": '',
            "enrolled_debt": '',
            "monthly_fee": '',
            "total_paid": '',
            "num_term_paid": '',
            "term_left": '',
            "balance": '',
            "payment_1st_date": ''
        }
        return result

    term = contract.term
    pymt_start = contract.payment_start_date
    term_left = term - contract.num_inst_completed
    balance = term_left * contract.monthly_fee 

    result = {
        "term": term,
        "total_debt" : contract.total_debt,
        "enrolled_debt": contract.enrolled_debt,
        "monthly_fee": contract.monthly_fee,
        "total_paid": contract.total_paid,
        "num_term_paid": contract.num_inst_completed,
        "term_left": term_left,
        "balance" : balance,
        "payment_1st_date": pymt_start.strftime('%Y-%m-%d'),
    }  

    return result
        


"""
Update Payment contract for a given client
"""
@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def update_payment_contract(client, data):

    combined_debts = fetch_client_combined_debts(client)
    if len(combined_debts) == 0:
        raise ValueError("No debts found") 

    # check if client has co-client associated with it
    co_sign = False
    if client.co_client:
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
    for record in combined_debts:
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
        planned_contract.credit_monitoring_fee = result['credit_monitoring_fee']
        planned_contract.bank_fee = result['bank_fee']
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

    ## allow docusign send for planned & approved contracts
    contract = DebtPaymentContract.query.filter(and_((DebtPaymentContract.client_id==client.id), 
                                                     or_(DebtPaymentContract.status==ContractStatus.PLANNED, 
                                                         DebtPaymentContract.status==ContractStatus.APPROVED)
                                                    )).first()
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
    if client.co_client and planned_contract.current_action != ContractAction.REMOVE_COCLIENT:
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
        'new_total_debt': round(planned_contract.total_debt, 2),
        'new_enrolled_debt': round(n_enrolled_debt, 2),
        'new_total_fee': round(n_total_fee, 2),
        'new_monthly_fee': round(n_monthly_fee, 2),
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

    # check if client has co-client associated with it
    co_sign = False
    if client.co_client:
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
            debt_line = CreditReportData.query.filter_by(public_id=item['public_id']).first()
            if debt_line is None:
                raise ValueError('Not avalid debt line')

            # check if change in the balance, MODIFY DEBT 
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
    # TERM CHANGE --- copy from the active debts
    elif action == ContractAction.TERM_CHANGE.name or action == ContractAction.NEW_EFT_AUTH.name:
        for item in active_contract.enrolled_debt_lines:
            planned_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=planned_contract.id,
                                                                         debt_id = item.debt_id).first()
            if planned_debt is None:
                planned_debt = DebtPaymentContractCreditData(contract_id=planned_contract.id,
                                                             debt_id=item.debt_id,
                                                             creditor=item.creditor,
                                                             account_number=item.account_number,
                                                             balance_original=float(item.balance_original),
                                                             )
                db.session.add(planned_debt)
                total_debt = total_debt + float(item.balance_original)
          

    planned_contract.total_debt = total_debt
    db.session.commit()

    result = fetch_amendment_plan(client) 
    planned_contract.enrolled_debt = result['new_enrolled_debt']
    planned_contract.monthly_fee = result['new_monthly_fee']
    planned_contract.credit_monitoring_fee = result['service_fee']
    planned_contract.bank_fee = result['bank_fee']
    # commit the changes
    db.session.commit()
    return result


@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def payment_contract_req4approve(user, client, data):
    action_title = data.get('action')
    note = data.get('note')
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

    svc_mgr = User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
    if svc_mgr is None:
        raise ValueError("Team Manager not found")

    contract.agent_id = requestor.id
    contract.status = ContractStatus.REQ4APPROVAL
    contract.current_action = action
    db.session.commit()
    ## create a Team Request
    team_request = create_team_request(requestor,
                                       svc_mgr,
                                       note,
                                       contract)
    return {
        'success': True,
        'message': 'Approval request submitted'
    }


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
    active_contract = DebtPaymentContract.query.filter_by(client_id=client.id, status=ContractStatus.ACTIVE).first()
    # not an error scenario
    if active_contract is None:
        return result

    initial_contract = DebtPaymentContract.query.filter_by(client_id=client.id, status=ContractStatus.REPLACED)\
                                                .order_by(asc(DebtPaymentContract.id)).first()
    if initial_contract is None:
        initial_contract = active_contract

    total_fee = initial_contract.monthly_fee * initial_contract.term
    total_fee = round(total_fee, 2)
    tmp = {
        'id': 0,
        'editable': False,
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
                                       .order_by(asc(DebtPaymentSchedule.id)).all()
    # error ?
    if len(records) == 0:
        #raise ValueError('Payment Schecule not found')
        return []

    index = 0
    balance = total_fee
    current_contract = initial_contract
    for record in records:
        if current_contract != record.contract:
            while True:
                next_contract = current_contract.next_contract
                if next_contract is None:
                    break
                item = _get_contract_description(next_contract, current_contract, balance)
                if item:
                    result.append(item)
                    balance = item['balance']

                if next_contract == record.contract:
                    break

                current_contract = next_contract

            current_contract = record.contract 

        index = index + 1
        balance = round(balance - record.amount, 2)

        eft_status = DebtEftStatus[record.status]
        item = {
            'id': record.id,
            'editable': False,
            'description': 'Payment {}'.format(index),
            'type': 'Payment',
            'status': eft_status.value,
            'plus' : '',
            'minus': record.amount, 
            'balance': balance,
            'trans_date': record.transaction.created_date.strftime("%m/%d/%Y") if record.transaction else '',
            'trans_id': record.transaction.trans_id if record.transaction else '',
            'proj_date': record.due_date.strftime("%m/%d/%Y"),
            'proj_amount': record.amount,
            'proj_balance': balance,
            'commission': '',
            'earned_fee': '', 
        }
        result.append(item)

        ## split rows
        credit_monitoring_fee = record.contract.credit_monitoring_fee
        misc_fee =  record.contract.bank_fee
        rehab_fee = round(record.amount - (credit_monitoring_fee + misc_fee), 2)

        item = {
            'id': record.id,
            'editable': False, 
            'description': 'Credit Monitoring',
            'type': 'Service Fee',
            'trans_date': record.transaction.created_date.strftime("%m/%d/%Y") if record.transaction else '',
            'earned_fee': credit_monitoring_fee,
        }
        result.append(item)
        item = {
            'id': record.id,
            'editable': False, 
            'description': 'Bank fee + Benefits',
            'type': 'Service Fee',
            'trans_date': record.transaction.created_date.strftime("%m/%d/%Y") if record.transaction else '',
            'earned_fee': misc_fee,
        }
        result.append(item)
        item = {
            'id': record.id,
            'editable': False, 
            'description': 'Credit Rehab',
            'type': 'Service Fee',
            'trans_date': record.transaction.created_date.strftime("%m/%d/%Y") if record.transaction else '',
            'earned_fee': rehab_fee,
        }
        result.append(item)

    return result

def _get_contract_description(new_contract, old_contract, balance):
    balance = round(balance, 2)
    new_balance = (new_contract.term - new_contract.num_inst_completed) * new_contract.monthly_fee
    new_balance = round(new_balance, 2)
    new_total_fee = new_contract.term * new_contract.monthly_fee
    
    type = ""
    desc = ""
    status = "Approved"
    minus = ""
    plus = ""
    if new_contract.current_action == ContractAction.REMOVE_DEBTS or \
       new_contract.current_action == ContractAction.RECIEVE_SUMMON:
        reduced = round(balance - new_balance, 2)
        desc = "Remove Debt <br />"
        type = "Remove Debt"
        if new_contract.current_action == ContractAction.RECIEVE_SUMMON:
            desc = "Receive Summon <br />"
            type = "Receive Summon"  
        desc = desc + "New Term: {} <br />".format(new_contract.term)
        desc = desc + "New Invoice Amount: ${} <br />".format(new_total_fee)
        desc = desc + "Removed Amount: ${} <br />".format(reduced)

        minus = reduced
    elif new_contract.current_action == ContractAction.ADD_DEBTS:
        reduced = round(new_balance - balance, 2)
        desc = "Add Debt <br />"
        desc = desc + "New Term: {} <br />".format(new_contract.term)
        desc = desc + "New Invoice Amount: ${} <br />".format(new_total_fee)
        desc = desc + "Added Amount: ${} <br />".format(reduced)
        type = "Add Debt"
        plus = reduced
    elif new_contract.current_action == ContractAction.MODIFY_DEBTS:
        desc = "Modify Debt <br />"
        desc = desc + "New Term: {} <br />".format(new_contract.term)
        desc = desc + "New Invoice Amount: ${} <br />".format(new_total_fee)
        diff = 0
        if new_balance > balance:
            diff = (new_balance - balance)
            diff = round(diff, 2)
            desc = desc + "Added Amount: ${} ".format(diff)
            plus = diff
        else:
            diff = (balance - new_balance)
            diff = round(diff, 2)
            desc = desc + "Removed Amount: ${} ".format(diff)
            minus = diff
        type = "Modify Debt"

    elif new_contract.current_action == ContractAction.TERM_CHANGE:
        type = "New term"
        desc = "Term Change <br />"
        desc = desc + "New Term: {} <br />".format(new_contract.term)
        desc = desc + "New Invoice Amount: ${} <br />".format(new_total_fee)
        diff = 0
        if new_balance > balance:
            diff = (new_balance - balance)
            diff = round(diff, 2)
            desc = desc + "Added Amount: ${}".format(diff)
            plus = diff
        else:
            diff = (balance - new_balance)
            diff = round(diff, 2)
            desc = desc + "Removed Amount: ${}".format(diff)
            minus = diff
    elif new_contract.current_action == ContractAction.ADD_COCLIENT:
        type = "Add Co-Client"
        desc = "Add Co-Client<br />"
        desc = desc + "New Term: {} <br />".format(new_contract.term)
        desc = desc + "New Invoice Amount: ${}<br />".format(new_total_fee)
        diff = (new_balance - balance)
        diff = round(diff, 2)
        desc = desc + "Added Amount: ${}".format(diff)
        plus = diff
    elif new_contract.current_action == ContractAction.REMOVE_COCLIENT:
        type = "Remove Co-Client"
        desc = "Remove Co-Client <br />"
        desc = desc + "New Term: {}<br />".format(new_contract.term)
        desc = desc + "New Invoice Amount: ${} <br />".format(new_total_fee)
        diff = (balance - new_balance)
        diff = round(diff, 2)
        desc = desc + "Removed Amount: ${}".format(diff)
        minus = diff
    elif new_contract.current_action == ContractAction.NEW_EFT_AUTH: 
        return None

        
    item = {
        'id': 0,
        'editable': False,
        'description': desc,
        'type': type,
        'status': status,
        'plus' : plus,
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

def update_payment_schedule(client, schedule_id, data):
    status = data.get('status')
    payment_schedule = DebtPaymentSchedule.query.outerjoin(DebtPaymentContract)\
                                                .filter(and_(DebtPaymentSchedule.id==schedule_id, DebtPaymentContract.client_id==client.id)).first() 
    if payment_schedule is None:
        raise ValueError("Schedule not found")
    
    contract = payment_schedule.contract
    if payment_schedule.status != status:
        state_handler = "ON_{}".format(status)
        try:
            func = getattr(payment_schedule, state_handler)
            func()
        except Exception as err:
            # state handler is not defined
            pass

    return {
       'success': True,
    }


## payment revision
@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def contract_open_revision(user, client, data):
    
    # revision method
    action = data.get('action')
    fields  = data.get('fields')
    note  = data.get('note')
    method = RevisionMethod[action]
    requestor = user

    # active contract
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.ACTIVE).first()
    if contract is None:
        raise ValueError("Active contract not found")

    
    cr = DebtPaymentContractRevision(contract_id=contract.id,
                                     agent_id=requestor.id,
                                     method=method,
                                     fields=fields)         
    db.session.add(cr)
    db.session.commit()

    svc_mgr = User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SERVICE_MGR.value).first()
    if svc_mgr is None:
        raise ValueError("Team Manager not found")

    create_team_request(requestor, svc_mgr, note, contract, cr) 

    return {
        'success': True,
        'message': 'Approval request submitted'
    }

## contract re-instate
@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def contract_reinstate(user, client, data):
    # fields
    fields  = data.get('fields')
    requestor = user

    # active contract
    contract = DebtPaymentContract.query.filter_by(client_id=client.id,
                                                   status=ContractStatus.ACTIVE).first()
    if contract is None:
        raise ValueError("Active contract not found")

    
    eft_required = False
    if 'is_update_bank_info' in fields and fields['is_update_bank_info'] is True:
        eft_required = True

    cr = DebtPaymentContractRevision(contract_id=contract.id,
                                     agent_id=requestor.id,
                                     method=RevisionMethod.RE_INSTATE,
                                     fields=fields,
                                     status=RevisionStatus.ACCEPTED)
    db.session.add(cr)
    db.session.commit()

    return {
        'success': True,
        'eft_required': eft_required,
    }

