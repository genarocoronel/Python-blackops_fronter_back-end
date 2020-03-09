from app.main import db
from app.main.service.docusign_service import DocuSign
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.main.model.client import Client, ClientDisposition
from app.main.model.credit_report_account import CreditPaymentPlan
from app.main.model.docsign import *
from app.main.model.credit_report_account import *
from app.main.model.address import Address, AddressType
from app.main.model.contact_number import ContactNumberType
from app.main.model.debt_payment import DebtPaymentContract, ContractStatus, DebtPaymentContractCreditData

from sqlalchemy import or_, and_

from flask import current_app as app

# scheduled task
# synchronize template details from Docusign account
def sync_templates():
    try: 
        ds = DocuSign()  
        # authorize the interface
        ds.authorize() 
        templates = ds.fetch_templates()
        for template in templates:
            key = template['id']
            name = template['name']
            # check if present in database
            exists = db.session.query(
                db.session.query(DocusignTemplate).filter_by(ds_key=key).exists()
            ).scalar()

            # if not, add to the database
            if not exists:
                ds_tmpl = DocusignTemplate(name=name, ds_key=key)
                db.session.add(ds_tmpl)
                db.session.commit()
                #print(ds_tmpl.id)
    except Exception as err:
        print("sync_templates task {}".format(str(err)))

# periodic task
# update signature status
def check_sessions():
    try:
        print("Inside Check Sessions")
        _docusign = DocuSign()
        _docusign.authorize()

        # fetch all docsuign session in progress
        sessions = DocusignSession.query.filter(or_(DocusignSession.status==DocusignSessionStatus.SENT, DocusignSession.status==DocusignSessionStatus.DELIVERED)).all()
        for session in sessions:
            contract = session.contract
            # fetch all in-progress sessions 
            #print(session.id)
            #print(session.state)

            status = session.status
            print(status)
            # if already completed state
            if (status == DocusignSessionStatus.COMPLETED) or (status == DocusignSessionStatus.DECLINED) or (status == DocusignSessionStatus.VOIDED):
                continue
            # fetch the envelope status 
            env_status = _docusign.envelope_status(session.envelope_id)
            new_status = _to_status(env_status)
            print(new_status)

            if new_status != status:
                # update client disposition

                #client = session.contract.client  
                #disposition = _to_disposition(env_status)
                #client.disposition_id = disposition.id
                #db.session.commit()

                # failed status
                if new_status == DocusignSessionStatus.DECLINED:
                    contract.status = ContractStatus.DECLINED 
                elif new_status == DocusignSessionStatus.VOIDED:
                    contract.status = ContractStatus.VOID
                elif new_status == DocusignSessionStatus.COMPLETED:
                    contract.status = ContractStatus.SIGNED

                session.status = new_status
                db.session.commit()
                     
    except Exception as err:
        print("Update signature status {}".format(str(err)))


def _to_status(status_txt):
    status_txt = status_txt.lower()
    result = DocusignSessionStatus.CREATED 
    if 'sent' in  status_txt:
        result = DocusignSessionStatus.SENT
    elif 'delivered' in status_txt:
       result = DocusignSessionStatus.DELIVERED
    elif 'completed' in status_txt:
       result = DocusignSessionStatus.COMPLETED
    elif 'declined' in status_txt:
       result = DocusignSessionStatus.DECLINED
    elif 'signed' in status_txt:
       result = DocusignSessionStatus.SIGNED
    elif 'voided' in status_txt:
       result = DocusignSessionStatus.VOIDED

    return result

def _to_disposition(status_txt):
    status_txt = status_txt.lower()
    result = "Contract Sent"
    if 'delivered' in status_txt:
        result = "Contract Opened"
    elif 'signed' in status_txt:
        result = "Contract Signed"
    elif 'completed' in status_txt:
        result = "Contract Completed"
    elif 'declined' in status_txt:
        result = "Contract Declined"
    elif 'voided' in status_txt:
        result = "Contract Voided"
    elif 'deleted' in status_txt:
        result = "Contract Deleted"
    
    print(result)
    cd = ClientDisposition.query.filter_by(value=result).first()    
    return cd

# test routines
def send_contract_for_signature(client_id):

    app.logger.info('Executing send contract for signature')

    try:
        t_params = {}

        cpp = CreditPaymentPlan.query.filter_by(name='Universal').first()
        if cpp is None:
            raise ValueError("Credit payment plan not present")
     
        credit_monitoring_fee = cpp.monitoring_fee_1signer
        bank_fee = cpp.monthly_bank_fee
        # fetch the lead object from the db
        client = Client.query.filter_by(id=client_id).first()
        # if client is not valid after session is created
        if client is None:
            raise ValueError("Client record not found")

        # check if client has co-client associated with it
        co_sign = False
        if client.client_id is not None:
            co_sign = True
            credit_monitoring_fee = cpp.monitoring_fee_2signer
            cc_id = client.client_id

        tmpl_name = 'EliteDMS_Contract_ 1Signed' 
        if co_sign is True:
            tmpl_name = 'EliteDMS_Contract_ 2Signed'

        ds_template = DocusignTemplate.query.filter_by(name=tmpl_name).first() 
        if ds_template is None:
            raise ValueError("Docusign template not found")

        ds_tmpl_id = ds_template.ds_key
        
        # Get the APPROVED contract for the client.
        payment_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
                                                               status=ContractStatus.APPROVED).first()
        if payment_contract is None:
            raise ValueError("Debt contract for client not found")

        # bank account
        bank_account = client.bank_account
        if bank_account is None:
            raise ValueError("Bank details not present for client")

        # fetch the address 
        client_address = Address.query.filter_by(client_id=client.id, type=AddressType.CURRENT).first()
        # fetch the phone numbers
        phone_numbers = {}
        client_contact_numbers = client.contact_numbers
        for ccn in client_contact_numbers:
            contact_number = ccn.contact_number
            number_type = ContactNumberType.query.filter_by(id=contact_number.contact_number_type_id).first()
            phone_numbers[number_type.name] = contact_number.phone_number
            

        client_full_name = '{} {}'.format(client.first_name, client.last_name)
        ssn4 = client.ssn[-4:] if client.ssn is not None else ""
        t_params['ClientFirstName'] = client.first_name
        t_params['ClientLastName'] = client.last_name 
        t_params['ClientHomePhone'] = phone_numbers['Home'] if 'Home' in phone_numbers else ""
        t_params['ClientWorkPhone'] = phone_numbers['Work Phone'] if 'Work Phone' in phone_numbers else ""
        t_params['ClientMobilePhone'] = phone_numbers['Cell Phone'] if 'Cell Phone' in phone_numbers else ""
        t_params['AcctOwnerMobile'] = phone_numbers['Cell Phone'] if 'Cell Phone' in phone_numbers else ""
        t_params['ClientEmail'] = client.email
        t_params['ClientDOB'] = client.dob.strftime("%m/%d/%Y") if client.dob is not None else ""
        t_params['AcctOwnerDOB'] = client.dob.strftime("%m/%d/%Y") if client.dob is not None else ""
        t_params['ClientLast4SSN'] = ssn4
        t_params['AcctOwnerName'] = bank_account.owner_name if bank_account.owner_name is not None else ""
        t_params['ClientFullName1'] = client_full_name
        t_params['ClientFullName2'] = client_full_name


        if client_address is not None:
            t_params['ClientAddress'] = client_address.address1
            t_params['ClientCity'] = client_address.city
            t_params['ClientState'] = client_address.state
            t_params['ClientZip'] = client_address.zip_code 
        else:
            t_params['ClientAddress'] = ''
            t_params['ClientCity'] = ''
            t_params['ClientState'] = ''
            t_params['ClientZip'] = ''

        t_params['BankName'] =  client.bank_account.bank_name
        t_params['BankRoutingNbr'] =  client.bank_account.routing_number
        t_params['BankAccountNbr'] = client.bank_account.account_number
        t_params['BankAccountType'] = client.bank_account.type.value
        t_params['AcctOwnerAddress'] = bank_account.address if bank_account.address is not None else ""
        t_params['AcctOwnerCity'] = bank_account.city if bank_account.city is not None else ""
        t_params['AcctOwnerState'] = bank_account.state if bank_account.state is not None else ""
        t_params['AcctOwnerZip'] = bank_account.zip if bank_account.zip is not None else ""
        t_params['AcctOwnerSSN'] =  bank_account.ssn if bank_account.ssn is not None else ""

        t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")
        t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")
        t_params['CurrentDate2'] = datetime.now().strftime("%m/%d/%Y")
        t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")
        t_params['CurrentDate102'] = datetime.now().strftime("%m/%d/%Y")
        t_params['CurrentDate3'] = datetime.now().strftime("%m/%d/%Y")
        t_params['CurrentDate4'] = datetime.now().strftime("%m/%d/%Y")
        tmp = datetime.now() + timedelta(days=7)
        t_params['7businessdaysafterCurrentDate'] = tmp.strftime("%m/%d/%Y")
        t_params['7businessdaysafterCurrentDate1'] = tmp.strftime("%m/%d/%Y")

        # debt tradelines for the contract 
        enrolled_debts = payment_contract.enrolled_debt_lines
        if enrolled_debts is None or (len(enrolled_debts) == 0): 
            raise ValueError("debt tradelines not present in the contract")

        n = 0
        total = 0
        for record in enrolled_debts:
            n = n + 1
            total = total + float(record.balance_original)
            t_params['Item{}'.format(n)] = str(n)
            t_params['Creditor{}'.format(n)] = record.creditor
            t_params['AccountNumber{}'.format(n)] = record.account_number
            t_params['BalanceOriginal{}'.format(n)] = record.balance_original
        # total
        t_params['PushTotal'] = "${:.2f}".format(total)

        # Repayment calculations
        pymt_term = payment_contract.term
        monthly_fee   = payment_contract.monthly_fee                             
        total_fee = (monthly_fee * pymt_term)

        savings_amount = monthly_fee
        t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
        t_params['SavingsAmount42'] = "${:.2f}".format(savings_amount)
        pymt_start = payment_contract.payment_start_date
        t_params['1stPaymentDate'] = pymt_start.strftime("%m/%d/%Y")
        t_params['1stPaymentDate10'] = pymt_start.strftime("%m/%d/%Y")
        # First payment 
        t_params['paymentNumber1'] = 1
        t_params['SavingsAmount1'] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate1'] = pymt_start.strftime("%m/%d/%Y")

        start = payment_contract.payment_recurring_begin_date
        for i in range(1, pymt_term):
            index = i + 1
            t_params['paymentNumber{}'.format(index)] = str(index)
            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(savings_amount)
            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y") 
            start = start + relativedelta(months=1)
        t_params['Term1'] = str(pymt_term)
        t_params['Term3'] = str(pymt_term)
        t_params['TotalSavingsAmount'] = "${:.2f}".format(total_fee)
        t_params['InvoiceAmount'] = "${:.2f}".format(total_fee)
        t_params['InvoiceAmount1'] = "${:.2f}".format(total_fee)

        t_params['BankFee1'] = "${:.2f}".format(credit_monitoring_fee)

        # co-sign related
        if co_sign is True:
            cc = Client.query.filter_by(id=cc_id).first()
            if cc is None:
                raise ValueError("Co-Client is not valid")

            ## find the co-client address
            cc_address = Address.query.filter_by(client_id=cc.id, type=AddressType.CURRENT).first()
            # fetch the phone numbers
            cc_phone_numbers = {}
            client_contact_numbers = cc.contact_numbers
            for ccn in client_contact_numbers:
                contact_number = ccn.contact_number
                number_type = ContactNumberType.query.filter_by(id=contact_number.contact_number_type_id).first()
                cc_phone_numbers[number_type.name] = contact_number.phone_number

            co_client_fname = '{} {}'.format(cc.first_name, cc.last_name)
            co_ssn4 = cc.ssn[-4:] if cc.ssn is not None else ""
            t_params['CoClientFirstName'] = cc.first_name
            t_params['CoClientLastName'] = cc.last_name
            t_params['CoClientHomePhone'] = cc_phone_numbers['Home'] if 'Home' in cc_phone_numbers else ""
            t_params['CoClientWorkPhone'] = cc_phone_numbers['Work Phone'] if 'Work Phone' in cc_phone_numbers else ""
            t_params['CoClientMobilePhone'] = cc_phone_numbers['Cell'] if 'Cell Phone' in cc_phone_numbers else ""
            t_params['CoClientEmail'] = cc.email if cc.email is not None else ""
            t_params['CoClientDOB'] = cc.dob.strftime("%m/%d/%Y") if cc.dob is not None else ""
            t_params['CoClientLast4SSN'] = co_ssn4
            t_params['CoClientFullName'] = co_client_fname
            t_params['CoClientFullName1'] = co_client_fname
            t_params['CoClientFullName2'] = co_client_fname

            if cc_address is not None:
                t_params['CoClientAddress'] = cc_address.address1
                t_params['CoClientCity'] = cc_address.city
                t_params['CoClientState'] = cc_address.state
                t_params['CoClientZip'] = cc_address.zip_code
            else:
                t_params['CoClientAddress'] = ''
                t_params['CoClientCity'] = ''
                t_params['CoClientState'] = ''
                t_params['CoClientZip'] = ''
               
        #Docusign interface
        ds = DocuSign()
        ds.authorize()
        # Send to primary client
        if co_sign is False:
            key = ds.request_signature(template_id=ds_tmpl_id,
                                       signer_name=client_full_name,
                                       signer_email=client.email,
                                       template_params=t_params,
                                       co_sign=False)
        else:
            key = ds.request_signature(template_id=ds_tmpl_id,
                                       signer_name=client_full_name,
                                       signer_email=client.email,
                                       template_params=t_params,
                                       co_sign=True,
                                       cosigner_name=co_client_fname,
                                       cosigner_email=cc.email)
       

        # create signature
        session = DocusignSession(template_id=ds_template.id,
                                  envelope_id=key,
                                  contract_id=payment_contract.id)
        db.session.add(session)
        db.session.commit()

        #disp = ClientDisposition.query.filter_by(value='Contract Sent').first()
        #client.disposition = disp
        #db.session.commit()

    except Exception as err:
        print("Error in sending contract {}".format(str(err))) 



def send_additional_debts_for_signature(client_id):
    try:
        t_params = {}

        cpp = CreditPaymentPlan.query.filter_by(name='Universal').first()
        if cpp is None:
            raise ValueError("Credit payment plan not present")

        credit_monitoring_fee = cpp.monitoring_fee_1signer
        bank_fee = cpp.monthly_bank_fee
        # fetch the lead object from the db
        client = Client.query.filter_by(id=client_id).first()
        # if client is not valid after session is created
        if client is None:
            raise ValueError("Client record not found")

        # check if client has co-client associated with it
        co_sign = False
        if client.client_id is not None:
            co_sign = True
            credit_monitoring_fee = cpp.monitoring_fee_2signer
            cc_id = client.client_id

        tmpl_name = 'Additional Debts'
        if co_sign is True:
            tmpl_name = 'Additional Debts_2Signer'

        ds_template = DocusignTemplate.query.filter_by(name=tmpl_name).first()
        if ds_template is None:
            raise ValueError("Docusign template not found")

        ds_tmpl_id = ds_template.ds_key

        # Get the APPROVED contract for the client.
        payment_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
                                                               status=ContractStatus.APPROVED).first()
        if payment_contract is None:
            raise ValueError("Debt contract for client not found")

        # Get the APPROVED contract for the client.
        active_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
                                                              status=ContractStatus.ACTIVE).first()
        if active_contract is None:
            raise ValueError("Active debt contract not found")

        additional_debts = []
        approved_debts = payment_contract.enrolled_debt_lines
        for debt in approved_debts:
            # find debts not present in the active contract
            active_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=active_contract.id, debt_id=debt.debt_id).first()
            if active_debt is None:
                additional_debts.append(debt)

        n = 0
        total = 0
        for record in additional_debts:
            n = n + 1
            total = total + float(record.balance_original)
            t_params['Item{}'.format(n)] = str(n)
            t_params['Creditor{}'.format(n)] = record.creditor
            t_params['AccountNumber{}'.format(n)] = record.account_number
            t_params['BalanceOriginal{}'.format(n)] = record.balance_original

        # total
        t_params['PushTotal'] = "${:.2f}".format(total)

        t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
        client_full_name = '{} {}'.format(client.first_name, client.last_name)
        t_params['ClientFullName'] = "{}".format(client_full_name)
        t_params['ClientFullName1'] = "{}".format(client_full_name)

        pymt_term = payment_contract.term
        total_fee = active_contract.total_paid + ((payment_contract.term - active_contract.num_inst_completed) * payment_contract.monthly_fee)
        
        monthly_fee = payment_contract.monthly_fee
        if active_contract.num_inst_completed > 0:
            monthly_fee = active_contract.monthly_fee     
        # First payment
        pymt_start = payment_contract.payment_start_date
        t_params['paymentNumber1'] = 1
        t_params['SavingsAmount1'] = "${:.2f}".format(monthly_fee)
        t_params['ProjectedDate1'] = pymt_start.strftime("%m/%d/%Y")

        start = payment_contract.payment_recurring_begin_date
        n = 0
        index = 1
        for i in range(1, active_contract.num_inst_completed):
            index = index + 1
            t_params['paymentNumber{}'.format(index)] = str(index)
            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(monthly_fee)
            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y")
            start = start + relativedelta(months=1)

        monthly_fee = payment_contract.monthly_fee
       
        for i in range(0, (pymt_term - active_contract.num_inst_completed)):
            index = index + 1
            t_params['paymentNumber{}'.format(index)] = str(index)
            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(monthly_fee)
            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y")
            start = start + relativedelta(months=1)
     
        t_params['SavingsAmount'] = "${:.2f}".format(monthly_fee)
        t_params['TotalSavingsAmount'] = "${:.2f}".format(total_fee)
        t_params['BankFee1'] = "${:.2f}".format(credit_monitoring_fee)
        if co_sign is True:
            cc = Client.query.filter_by(id=cc_id).first()
            t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
            t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
        
        #Docusign interface
        ds = DocuSign()
        ds.authorize()
        # Send to primary client
        if co_sign is False:
            key = ds.request_signature(template_id=ds_tmpl_id,
                                       signer_name=client_full_name,
                                       signer_email=client.email,
                                       template_params=t_params,
                                       co_sign=False)
        else:
            key = ds.request_signature(template_id=ds_tmpl_id,
                                       signer_name=client_full_name,
                                       signer_email=client.email,
                                       template_params=t_params,
                                       co_sign=True,
                                       cosigner_name=co_client_fname,
                                       cosigner_email=cc.email)


        # create signature
        session = DocusignSession(template_id=ds_template.id,
                                  envelope_id=key,
                                  contract_id=payment_contract.id)
        db.session.add(session)
        db.session.commit()


    except Exception as err:
        print("Error in sending add debts contract {}".format(str(err)))

def send_removal_debts_for_signature(client_id):
    try:
        t_params = {}

        cpp = CreditPaymentPlan.query.filter_by(name='Universal').first()
        if cpp is None:
            raise ValueError("Credit payment plan not present")

        credit_monitoring_fee = cpp.monitoring_fee_1signer
        bank_fee = cpp.monthly_bank_fee
        # fetch the lead object from the db
        client = Client.query.filter_by(id=client_id).first()
        # if client is not valid after session is created
        if client is None:
            raise ValueError("Client record not found")

        # check if client has co-client associated with it
        co_sign = False
        co_client = client.co_client
        if co_client:
            co_sign = True
            credit_monitoring_fee = cpp.monitoring_fee_2signer

        tmpl_name = 'Removal Debts'
        if co_sign is True:
            tmpl_name = 'Removal Debts 2Signer'

        ds_template = DocusignTemplate.query.filter_by(name=tmpl_name).first()
        if ds_template is None:
            raise ValueError("Docusign template not found")

        ds_tmpl_id = ds_template.ds_key
        # Get the APPROVED contract for the client.
        payment_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
                                                               status=ContractStatus.APPROVED).first()
        if payment_contract is None:
            raise ValueError("Debt payment plan for the client not found")
        # Get the APPROVED contract for the client.
        active_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
                                                              status=ContractStatus.ACTIVE).first()
        if active_contract is None:
            raise ValueError("Active payment contract not found")

        removal_debts = []
        active_debts = active_contract.enrolled_debt_lines
        for debt in active_debts:
            # find debts not present in the active contract
            planned_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=payment_contract.id, debt_id=debt.debt_id).first()
            if planned_debt is None:
                removal_debts.append(debt)

        n = 0
        total = 0
        for record in removal_debts:
            n = n + 1
            total = total + float(record.balance_original)
            t_params['Item{}'.format(n)] = str(n)
            t_params['Creditor{}'.format(n)] = record.creditor
            t_params['AccountNumber{}'.format(n)] = record.account_number
            t_params['BalanceOriginal{}'.format(n)] = record.balance_original

        # total
        t_params['PushTotal'] = "${:.2f}".format(total)

        t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
        client_full_name = '{} {}'.format(client.first_name, client.last_name)
        t_params['ClientFullName'] = "{}".format(client_full_name)
        t_params['ClientFullName1'] = "{}".format(client_full_name)

        pymt_term = payment_contract.term
        total_fee = active_contract.total_paid + ((payment_contract.term - active_contract.num_inst_completed) * payment_contract.monthly_fee)
        
        monthly_fee = payment_contract.monthly_fee
        if active_contract.num_inst_completed > 0:
            monthly_fee = active_contract.monthly_fee     
        # First payment
        pymt_start = payment_contract.payment_start_date
        t_params['paymentNumber1'] = 1
        t_params['SavingsAmount1'] = "${:.2f}".format(monthly_fee)
        t_params['ProjectedDate1'] = pymt_start.strftime("%m/%d/%Y")

        start = payment_contract.payment_recurring_begin_date
        n = 0
        index = 1
        for i in range(1, active_contract.num_inst_completed):
            index = index + 1
            t_params['paymentNumber{}'.format(index)] = str(index)
            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(monthly_fee)
            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y")
            start = start + relativedelta(months=1)

        monthly_fee = payment_contract.monthly_fee
        print(pymt_term)
       
        for i in range(0, (pymt_term - active_contract.num_inst_completed)):
            index = index + 1
            t_params['paymentNumber{}'.format(index)] = str(index)
            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(monthly_fee)
            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y")
            start = start + relativedelta(months=1)
     
        t_params['SavingsAmount'] = "${:.2f}".format(monthly_fee)
        t_params['TotalSavingsAmount'] = "${:.2f}".format(total_fee)
        t_params['BankFee1'] = "${:.2f}".format(credit_monitoring_fee)
        if co_client:
            co_client_fullname = '{} {}'.format(co_client.first_name, co_client.last_name)
            t_params['CoClientFullName'] = "{}".format(co_client_fullname)
            t_params['CoClientFullName1'] = "{}".format(co_client_fullname)
        
        #Docusign interface
        ds = DocuSign()
        ds.authorize()
        # Send to primary client
        if co_sign is False:
            key = ds.request_signature(template_id=ds_tmpl_id,
                                       signer_name=client_full_name,
                                       signer_email=client.email,
                                       template_params=t_params,
                                       co_sign=False)
        else:
            key = ds.request_signature(template_id=ds_tmpl_id,
                                       signer_name=client_full_name,
                                       signer_email=client.email,
                                       template_params=t_params,
                                       co_sign=True,
                                       cosigner_name=co_client_fname,
                                       cosigner_email=cc.email)
        # create signature
        session = DocusignSession(template_id=ds_template.id,
                                  envelope_id=key,
                                  contract_id=payment_contract.id)
        db.session.add(session)
        db.session.commit()


    except Exception as err:
        print("Error in sending add debts contract {}".format(str(err)))

#def send_modify_debts_for_signature(session_id):
#    try:
#        app.logger.info('Send Modify Debts  for signature')
#
#        t_params = {}
#
#        session = DocusignSession.query.filter_by(id=session_id).first()
#        if session is None:
#            raise ValueError("Session is not present, session id is not valid")
#        client_id = session.client_id
#        ds_tmpl_id = session.template.ds_key
#
#        # fetch the client from db
#        client = Client.query.filter_by(id=client_id).first()
#        # check if client has co-client associated with it
#        co_sign = False
#        if client.client_id is not None:
#            co_sign = True
#            cc_id = client.client_id
#
#        # Get the APPROVED contract for the client.
#        approved_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
#                                                                status=ContractStatus.APPROVED).first()
#        if approved_contract is None:
#            raise ValueError("Modified debt contract not found") 
#
#        # Get the APPROVED contract for the client.
#        active_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
#                                                              status=ContractStatus.ACTIVE).first()
#        if active_contract is None:
#            raise ValueError("Active debt contract not found") 
#
#        client_full_name = '{} {}'.format(client.first_name, client.last_name)
#        t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
#        t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
#        t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
#        t_params['ClientFullName'] = client_full_name
#        t_params['ClientFullName1'] = client_full_name
#
#
#        modified_debts = []
#        approved_debts = approved_contract.enrolled_debt_lines
#        for debt in approved_debts:
#            active_debt = DebtPaymentContractCreditData.query.filter_by(contract_id=active_contract.id, debt_id=debt.debt_id).first()
#            # find the debt in active 
#            if active_debt.balance_original != debt.balance_original:
#                modified_debts.append(debt)
#
#        n = 0
#        total = 0
#        for record in modify_debts:
#            n = n + 1
#            total = total + float(record.balance_original)
#
#            t_params['Creditor{}'.format(n)] = record.creditor
#            t_params['AccountNumber{}'.format(n)] = record.account_number
#            t_params['BalanceOriginal{}'.format(n)] = record.balance_original
#        # total
#        t_params['PushTotal'] = "${:.2f}".format(total)
#
#        # Repayment calculations
#        pymt_term = approved_contract.term
#        enrolled_debt = approved_contract.enrolled_debt
#        credit_monitoring_fee = approved_contract.credit_monitoring_fee
#        monthly_fee   = approved_contract.monthly_fee
#        total_fee = (monthly_fee * pymt_term)
#        # monthly_bank_fee = credit_plan.monthly_bank_fee
#        # min_allowed_fee = credit_plan.minimum_fee  
#        savings_amount = monthly_fee
#        t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
#        pymt_start = approved_contract.payment_start_date
#        start = pymt_start
#
#        n = 0
#        for i in range(0, active_contract.num_inst_completed):
#            index = i + 1
#            n = i
#            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(active_contract.monthly_fee)
#            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y") 
#            start = start + relativedelta(months=1)
#
#        for i in range(n, (pymt_term - active_contract.num_inst_completed)):
#            index = i + 1
#            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(savings_amount)
#            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y") 
#            start = start + relativedelta(months=1)
#            
#        t_params['TotalSavingsAmount'] = "${:.2f}".format(total_fee)
#        t_params['BankFee1'] = credit_monitoring_fee
#        # co client informaton
#        if co_sign is True:
#            cc = Client.query.filter_by(id=cc_id).first()
#            co_client_fname = '{} {}'.format(cc.first_name, cc.last_name)
#            t_params['CoClientFullName'] = co_client_fname
#            t_params['CoClientFullName1'] = co_client_fname
#        
#        ds = DocuSign()
#        ds.authorize()
#
#        if co_sign is False:
#            key = ds.request_signature(template_id=ds_tmpl_id,
#                                       signer_name=client_full_name,
#                                       signer_email=client.email,
#                                       template_params=t_params,
#                                       co_sign=False)
#        else:
#            key = ds.request_signature(template_id=ds_tmpl_id,
#                                       signer_name=client_full_name,
#                                       signer_email=client.email,
#                                       template_params=t_params,
#                                       co_sign=True,
#                                       cosigner_name=co_client_fname,
#                                       cosigner_email=cc.email)
#
#
#        # create signature
#        signature = DocusignSignature(envelope_id=key,
#                                      status=DocusignSessionStatus.SENT,
#                                      modified=datetime.utcnow(),
#                                      session_id=session.id)
#
#        db.session.add(signature)
#        db.session.commit()
#
#        # add client disposition
#
#    except Exception:
#        print("Error in send modify debts")
#
#def send_term_change_for_signature(client_id):
#
#    t_params = {}
#
#    # fetch the client from db
#    client = Client.query.filter_by(id=client_id).first()
#    co_sign = False
#    if client.client_id is not None:
#        co_sign = True
#        cc_id = client.client_id
#
#    # Get the APPROVED contract for the client.
#    payment_contract = DebtPaymentContract.query.filter_by(client_id=client_id,
#                                                           status=ContractStatus.APPROVED).first()
#    if payment_contract is None:
#        raise ValueError("Debt contract for client not found")
#
#    t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
#    t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
#    t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
#    
#    client_full_name = '{} {}'.format(client.first_name, client.last_name)
#    t_params['ClientFullName'] = client_full_name
#    t_params['ClientFullName1'] = client_full_name
#    
#    # Repayment calculations
#    pymt_term = payment_contract.term
#    enrolled_debt = payment_contract.enrolled_debt
#    monthly_fee   = payment_contract.monthly_fee
#    credit_monitoring_fee = contract.credit_monitoring_fee
#    total_fee = (monthly_fee * pymt_term)
#
#    savings_amount = payment_contract.monthly_fee
#    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
#
#    pymt_start = payment_contract.payment_start_date
#    # First payment
#    t_params['paymentNumber1'] = 1
#    t_params['SavingsAmount1'] = "${:.2f}".format(savings_amount)
#    t_params['ProjectedDate1'] = pymt_start.strftime("%m/%d/%Y")
#
#    start = payment_contract.payment_recurring_begin_date
#    for i in range(1, pymt_term):
#        index = i + 1
#        t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(savings_amount)
#        t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y") 
#        start = start + relativedelta(months=1)
#        
#    t_params['TotalSavingsAmount'] = "${:.2f}".format(total_fee)
#    t_params['BankFee1'] = "${:.2f}".format(credit_monitoring_fee)
#    if co_sign is True:
#        cc = Client.query.filter_by(id=cc_id).first()
#        t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
#        t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
#    
#    #Docusign interface
#    ds = DocuSign()
#    ds.authorize()
#
#    if co_sign is False:
#        key = ds.request_signature(template_id=ds_tmpl_id,
#                                   signer_name=client_full_name,
#                                   signer_email=client.email,
#                                   template_params=t_params,
#                                   co_sign=False)
#    else:
#        key = ds.request_signature(template_id=ds_tmpl_id,
#                                   signer_name=client_full_name,
#                                   signer_email=client.email,
#                                   template_params=t_params,
#                                   co_sign=True,
#                                   cosigner_name=co_client_fname,
#                                   cosigner_email=cc.email)


#
#def send_receive_summon_for_signature(client_id,
#                                      cc_id,
#                                      co_sign=False,
#                                      savings_amount=688.20,
#                                      num_savings=30):
#
#    t_params = {}
#
#    ds = DocuSign()
#    ds.authorize()
#    if co_sign is True:
#        tid = receive_summon2_id
#    else:
#        tid = receive_summon1_id
#
#    # fetch the client from db
#    client = Client.query.filter_by(id=client_id).first()
#
#    n = 0
#    total = 0
#    for c in _credit_data:
#        n = n + 1
#        total = total + c[2]
#        t_params['Creditor{}'.format(n)] = c[0] 
#        t_params['AccountNumber{}'.format(n)] = c[1] 
#        t_params['BalanceOriginal{}'.format(n)] = "${:.2f}".format(c[2])
#    # total
#    t_params['PushTotal'] = "${:.2f}".format(total)
#
#    t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
#    t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
#    t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
#    t_params['ClientFullName'] = "{} {}".format(client.first_name, client.last_name)
#    t_params['ClientFullName1'] = "{} {}".format(client.first_name, client.last_name)
#    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
#    start = datetime(2019, 12, 15)
#    for i in range(1,31):
#        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
#        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
#        start = start + relativedelta(months=1)
#        
#    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
#    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
#    if co_sign is True:
#        cc = Client.query.filter_by(id=cc_id).first()
#        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
#        t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
#        t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
#    
#    key = ds.request_signature(template_id=tid,
#                               signer_name="{} {}".format(client.first_name, client.last_name),
#                               signer_email=client.email,
#                               template_params=t_params)
#
