# EPPS tasks
from app.main.model.client import Client
from app.main.service.epps_service import *
from app.main.model.debt_payment import DebtEftStatus, DebtPaymentSchedule, DebtPaymentTransaction
from datetime import datetime, date, timedelta
from sqlalchemy import func

import logging

from app.main import db
"""
API to register a customer with EPPS provider
@@params
@client_id --> Client Identifier
"""
def register_customer(client_id):
    try:
        client = Client.query.filter_by(public_id=client_id).first()
        if client is None:
            raise ValueError("Client not found")

        card = CardHolder()
        card.id = client.public_id
        card.first_name = client.first_name
        card.last_name = client.last_name
        card.dob = client.dob
        card.ssn = client.ssn
        card.street = client.address
        card.city = client.city
        card.state = client.state
        card.zip = client.zip
        card.phone = client.phone
        card.email = client.email

        epps_chnl = EppsClient()
        epps_chnl.connect()
        # Add the customer
        epps_chnl.add_card_holder(card)

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
        payments = DebtPaymentSchedule.query.filter(func.date(DebtPaymentSchedule.due_date)==due).all()
        for payment in payments:
            print(payment.id)
            client = payment.client
            bank_account = client.bank_account
            # EFT Request parameters
            eft = Eft() 	
            eft.id = client.public_id
            eft.date = payment.due_date
            eft.amount = payment.amount
            # EFT fee ??
            eft.fee = payment.amount
            eft.bank_name = bank_account.name
            if bank_account.city is not None:
                eft.bank_city = bank_account.city
            if bank_account.state is not None:
                eft.bank_state = bank_account.state
            eft.account_no = bank_account.account_number
            eft.routing_no = bank_account.routing_number
            eft.account_type = bank_account.type.value
            eft.memo = "Debt EFT request"

            response = epps_chnl.register_eft(eft)
            # create a transaction 
            if response.status == EftStatus.Failed or response.status == EftStatus.Error:
                trans_id = 0
                payment.status = DebtEftStatus.Failed
            elif response.status == EftStatus.Returned or response.status == EftStatus.Voided:
                trans_id = 0
                payment.status = DebtEftStatus.Failed
            elif response.status == EftStatus.Settled:
                trans_id = response.transaction_id
                payment.status = DebtEftStatus.Settled
            else:
                print("Successful EFT request")
                print(response.status)
                print(response.message)
                trans_id = response.transaction_id
                # update the payment schedule
                payment.status = DebtEftStatus.Processed

            transaction = DebtPaymentTransaction(trans_id=trans_id,
                                                 status=response.status.value,
                                                 message=response.message,
                                                 payment_id=payment.id)
            db.session.add(transaction)
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
        payments = DebtPaymentSchedule.query.filter_by(status=DebtEftStatus.Processed).all()
        if payments is None or len(payments) == 0:
            return 
        for payment in payments:
            #fetch transaction
            print(payment.id)
            for eft_transaction in payment.transactions:
                eft = epps_chnl.find_eft_by_transaction(eft_transaction.trans_id)
                if eft.status.value != eft_transaction.status: 
                    eft_transaction.status = eft.status.value 
                    eft_transaction.modified_date = datetime.utcnow()
                    eft_transaction.message = eft.message
                    if eft.status == EftStatus.Failed or eft.status == EftStatus.Error:
                        payment.status = DebtEftStatus.Failed
                    elif eft.status == EftStatus.Settled:
                        payment.status = DebtEftStatus.Settled
                    elif eft.status == EftStatus.Returned or eft.status == EftStatus.Voided:
                        payment.status = DebtEftStatus.Failed
                      
            # db session commit
            db.session.commit()

    except Exception as err:    
        logging.warning("Check EFT Status issue {}".format(str(err)))
        
