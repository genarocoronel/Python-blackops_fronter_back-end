# EPPS tasks
from app.main.model.client import Client
from app.main.service.epps_service import *
from app.main.model.debt_payment import DebtEftStatus, DebtPaymentSchedule, DebtPaymentTransaction
from app.main.model.contact_number import ContactNumberType
from app.main.model.address import Address, AddressType
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_, and_
import app.main.tasks.mailer as mailer
import app.main.service.workflow as workflow

import logging

from app.main import db
"""
API to register a customer with EPPS provider
@@params
@client_id --> Client Identifier
"""
def register_customer(client_id):
    try:
        client = Client.query.filter_by(id=client_id).first()
        if client is None:
            raise ValueError("Client not found")
 
        ## client address
        client_address = Address.query.filter_by(client_id=client.id, type=AddressType.CURRENT).first()
        if client_address is None:
            raise ValueError("Client Address is not found")
        if client.dob is None:
            raise ValueError("Client DOB is required for EPPS registration")

        # fetch the phone numbers
        phone_numbers = {}
        client_contact_numbers = client.contact_numbers
        for ccn in client_contact_numbers:
            contact_number = ccn.contact_number
            number_type = ContactNumberType.query.filter_by(id=contact_number.contact_number_type_id).first()
            phone_numbers[number_type.name] = contact_number.phone_number

        ## create a unique id
        cid = '{:>07d}'.format(client.id)
        cc_id = '222'
        cardId = '{}{}'.format(cc_id, cid)

        card = CardHolder()
        card.id = cardId
        card.first_name = client.first_name
        card.last_name = client.last_name
        card.dob = client.dob
        card.ssn = client.ssn if client.ssn else ''
        card.street = client_address.address1
        card.city = client_address.city
        card.state = client_address.state
        card.zip = client_address.zip_code
        card.email = client.email
        if 'Cell Phone' in phone_numbers:
            card.phone = phone_numbers['Cell Phone']
        elif 'Home' in phone_numbers:
            card.phone = phone_numbers['Home']
        elif 'Work Phone' in phone_numbers:
            card.phone = phone_numbers['Work Phone']

        epps_chnl = EppsClient()
        epps_chnl.connect()
        # Add the customer
        epps_chnl.add_card_holder(card)

        # EPPS Account holder Id
        client.epps_account_id = cardId
        db.session.commit()

    except Exception as err:
        logging.warning("Register customer issue {}".format(str(err)))
        return None

"""
scheduler routine to register EFT requests with EPPS
Run the scheduler at midnight
fetch all the payments, and register EFT with EPPS provider.
"""
def process_debt_payments():
    try:
        epps_chnl = EppsClient()
        epps_chnl.connect()

        # fetch all today's payments 
        due = date.today() + timedelta(days=3)
        payments = DebtPaymentSchedule.query\
                                      .filter(and_(func.date(DebtPaymentSchedule.due_date)==due, DebtPaymentSchedule.status==DebtEftStatus.FUTURE.name)).all()
        for payment in payments:
            print(payment.id)
            contract = payment.contract
            if not contract:
                continue
            client = contract.client
            if not client:
                continue
            bank_account = client.bank_account
            if not bank_account:
                continue
            if client.status_name == 'Service_ActiveStatus_NSF' or client.status_name == 'Sales_ActiveStatus_NSF':
                continue
            transaction = payment.transaction
            if transaction and \
              (transaction.status == EftStatus.Pending.value or transaction.status == EftStatus.Settled.value):
                continue
                 
            ## create a unique id
            cardId = client.epps_account_id
            # EFT Request parameters
            eft = Eft() 	
            eft.id = cardId
            eft.date = payment.due_date
            eft.amount = payment.amount
            # EFT fee ??
            eft.fee = payment.amount

            eft.bank_name = bank_account.bank_name
            if bank_account.city:
                eft.bank_city = bank_account.city
            if bank_account.state:
                eft.bank_state = bank_account.state
            eft.account_no = bank_account.account_number
            eft.routing_no = bank_account.routing_number
            eft.account_type = bank_account.type.value
            eft.memo = "Debt EFT request"

            response = epps_chnl.register_eft(eft)
            # create a transaction 
            if response.status == EftStatus.Failed or response.status == EftStatus.Error:
                trans_id = 0
                payment.status = DebtEftStatus.NSF.name
            elif response.status == EftStatus.Returned or response.status == EftStatus.Voided:
                trans_id = 0
                payment.status = DebtEftStatus.NSF.name
            elif response.status == EftStatus.Settled:
                trans_id = response.transaction_id
                payment.status = DebtEftStatus.CLEARED.name
            else:
                # print(response.status)
                # print(response.message)
                trans_id = response.transaction_id
                # update the payment schedule
                payment.status = DebtEftStatus.SEND_TO_EFT.name

            if not transaction:
                transaction = DebtPaymentTransaction(trans_id=trans_id,
                                                     status=response.status.value,
                                                     message=response.message,
                                                     payment_id=payment.id)
                db.session.add(transaction)
            else:
                transaction.trans_id = trans_id
                transaction.status = response.status.value
                transaction.message = response.message
            
            db.session.commit()
                
    except Exception as err:
        logging.warning("Add EFT task issue {}".format(str(err)))

"""
task routine to check the status of EFTs send to EPPS
@@params None
@@result updates the status of each 'Processed' Payment. 
"""
def check_eft_status():
    try:
        epps_chnl = EppsClient()
        epps_chnl.connect()
        
        # fetch all the EFT transactions
        payments = DebtPaymentSchedule.query.filter(or_(DebtPaymentSchedule.status==DebtEftStatus.SEND_TO_EFT.name,
                                                        DebtPaymentSchedule.status==DebtEftStatus.TRANSMITTED.name)).all()
        for payment in payments:
            client = payment.contract.client
            #fetch transaction
            print(payment.id)
            eft_transaction = payment.transaction
            if eft_transaction:
                eft = epps_chnl.find_eft_by_transaction(eft_transaction.trans_id)
                if eft.status.value != eft_transaction.status: 
                    eft_transaction.status = eft.status.value 
                    eft_transaction.modified_date = datetime.utcnow()
                    eft_transaction.message = "{} - {} ".format(eft.code, eft.message)
                    contract = payment.contract                        

                    if eft.status == EftStatus.Transmitted:
                        payment.on_eft_transmitted()
                    elif eft.status == EftStatus.Failed or eft.status == EftStatus.Error:
                        payment.on_eft_failed()
                        wflow = workflow.NSFWorkflow(contract)
                        wflow.on_failure()
                    elif eft.status == EftStatus.Returned or eft.status == EftStatus.Voided:
                        payment.on_eft_failed()
                        wflow = workflow.NSFWorkflow(contract)
                        wflow.on_failure()
                    elif eft.status == EftStatus.Settled:
                        payment.on_eft_settled()
                      
            # db session commit
            db.session.commit()

    except Exception as err:    
        logging.warning("Check EFT Status issue {}".format(str(err)))
        


def process_upcoming_payments():
    """
    task routine to send payment reminder to clients
    @@ params: None
    @@ result: send payment reminder notification to client
    """
    
    ## 5 day advance notice
    d5_adv_date = date.today() + timedelta(days=5) 
    payments = DebtPaymentSchedule.query.filter(func.date(DebtPaymentSchedule.due_date)==d5_adv_date).all()
    for payment in payments:
        try:
            contract = payment.contract
            client = contract.client
            if client.status_name == 'Service_ActiveStatus_NSF' or client.status_name == 'Sales_ActiveStatus_NSF':
                continue
            # send 5 day payment reminder notice
            mailer.send_payment_reminder(contract.client_id,
                                         payment.id)

            # send 5 day reminder SMS
            mailer.send_sms_payment_reminder(contract.client_id,
                                             payment.id)

        except Exception:
            continue 

    # 2 Day reminder
    due_date = date.today() + timedelta(days=2)
    payments = DebtPaymentSchedule.query.filter(func.date(DebtPaymentSchedule.due_date)==due_date).all()
    for payment in payments:
        try:
            contract = payment.contract
            client = contract.client
            if client.status_name == 'Service_ActiveStatus_NSF' or client.status_name == 'Sales_ActiveStatus_NSF':
                continue
            # send 2 day reminder SMS
            mailer.send_sms_payment_reminder(contract.client_id,
                                             payment.id)

        except Exception:
            continue

    # 1 Day reminder
    due_date = date.today() + timedelta(days=1)
    payments = DebtPaymentSchedule.query.filter(func.date(DebtPaymentSchedule.due_date)==due_date).all()
    for payment in payments:
        try:
            contract = payment.contract
            client = contract.client
            if client.status_name == 'Service_ActiveStatus_NSF' or client.status_name == 'Sales_ActiveStatus_NSF':
                continue
            # send 1 day reminder SMS
            mailer.send_sms_payment_reminder(contract.client_id,
                                             payment.id)

        except Exception:
            continue
    

