from datetime import datetime
from app.main import db
from app.main.model.credit_report_account import CreditReportData, CreditPaymentPlan
from app.main.model.client import Client
from app.main.model.debt_payment import DebtPaymentSchedule, DebtEftStatus
from dateutil.relativedelta import relativedelta
from sqlalchemy import and_

import logging

from flask import current_app as app
"""
Generate Debt Payment schedule for the client
Called after Document signature/s are completed.
"""
def create_debt_payment_schedule(client_id):
    try:
        client = Client.query.filter_by(id=client_id).first()
        if client is None:
            raise ValueError("Client Not Found")
        credit_plan = CreditPaymentPlan.query.filter_by(name='Universal').first()
        if credit_plan is None:
            raise ValueError("Credit payment plan not present")
        # check if client has co-client associated with it
        co_sign = False
        if client.client_id is not None:
            co_sign = True
        # credit report
        credit_report = client.credit_report_account
        if credit_report is None:
            raise ValueError("Credit report for client not found")
        # credit records 
        credit_records = credit_report.records
        if credit_records is None or len(credit_records) == 0:
            raise ValueError("Credit records are empty")
        # calculate the debt
        total = 0
        for record in credit_records:
            total = total + float(record.balance_original)
        # calculations
        total_debt = total
        debt_enrolled_percent = credit_plan.enrolled_percent
        credit_monitoring_fee = credit_plan.monitoring_fee_1signer
        if co_sign is True:
            credit_monitoring_fee = credit_plan.monitoring_fee_2signer
        monthly_bank_fee = credit_plan.monthly_bank_fee
        min_allowed_fee = credit_plan.minimum_fee
        term = credit_report.term
        total_fee = (total_debt * (debt_enrolled_percent/100)) + (credit_monitoring_fee * term) + (monthly_bank_fee * term)
        total_fee = round(total_fee, 2)
        if total_fee < min_allowed_fee:
            total_fee = min_allowed_fee
        # monthly fee
        monthly_fee = round((total_fee / term), 2)
        pymt_start  = credit_report.payment_start_date
        dps = DebtPaymentSchedule(client_id=client_id,
                                  due_date=pymt_start,
                                  amount=monthly_fee,
                                  bank_fee=monthly_bank_fee)
        db.session.add(dps)
        db.session.commit()
        start = credit_report.payment_recurring_begin_date
        for i in range(1, term):
            dps = DebtPaymentSchedule(client_id=client_id,
                                      due_date=start,
                                      amount=monthly_fee,
                                      bank_fee=monthly_bank_fee)
            db.session.add(dps)
            db.session.commit()
            # add the schedule record
            start = start + relativedelta(months=1)
        # commit 
        db.session.commit()
    except Exception as err:
        logging.warning("Create Debt Payment Schedule issue {}".format(str(err)))

def create_debt_payment_account(client_id):
    try:
        client = Client.query.filter_by(public_id=client_id).first()   
        if client is None:
            raise ValueError("Client not found")
        # data integrity check
        # check if already debt payment schedule is present
        # if so, only modification is available
        scheduled = DebtPaymentSchedule.query.filter_by(client_id=client.id, status=DebtEftStatus.Scheduled).all()
        if len(scheduled) > 0:
            raise ValueError("Debt Payment is already in progress")

        # create debt payment schedule
        create_debt_payment_schedule(client.id)

        # send to worker queue
        func = "register_customer"
        app.queue.enqueue('app.main.tasks.debt_payment.{}'.format(func), client_id)

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
