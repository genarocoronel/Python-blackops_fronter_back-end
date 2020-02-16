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
        sessions = DocusignSession.query.filter_by(state=SessionState.PROGRESS).all()
        for session in sessions:
            # fetch all in-progress sessions 
            #print(session.id)
            #print(session.state)
            signature = session.signature
            completed = True 

            status = signature.status
            print(status)
            # if already completed state
            if (status == SignatureStatus.COMPLETED) or (status == SignatureStatus.DECLINED) or (status == SignatureStatus.VOIDED):
                continue
            # fetch the envelope status 
            env_status = _docusign.envelope_status(signature.envelope_id)
            new_status = _to_status(env_status)
            print(new_status)

            if new_status != status:
                # update client disposition
                client = Client.query.filter_by(id=session.client_id).first()
                disposition = _to_disposition(env_status)
                client.disposition_id = disposition.id
                db.session.commit()

                if (new_status == SignatureStatus.CREATED) or (new_status == SignatureStatus.SENT):
                    completed = False
                ## intermediary status DELIVERED/SIGNED
                elif (new_status == SignatureStatus.DELIVERED) or (new_status == SignatureStatus.SIGNED):
                    completed = False
                # failed status
                elif (new_status == SignatureStatus.DECLINED) or (new_status == SignatureStatus.VOIDED):
                    session.state = SessionState.FAILED
                    signature.status = new_status
                    db.session.commit()
                    break 
            else:
                completed = False
                continue
               
            signature.status = new_status
            db.session.commit()
            
            if (completed is True) and (session.state == SessionState.PROGRESS):
                session.state = SessionState.COMPLETED
                db.session.commit()
                     
    except Exception as err:
        print("Update signature status {}".format(str(err)))


def _to_status(status_txt):
    status_txt = status_txt.lower()
    result = SignatureStatus.CREATED 
    if 'sent' in  status_txt:
        result = SignatureStatus.SENT
    elif 'delivered' in status_txt:
       result = SignatureStatus.DELIVERED
    elif 'completed' in status_txt:
       result = SignatureStatus.COMPLETED
    elif 'declined' in status_txt:
       result = SignatureStatus.DECLINED
    elif 'signed' in status_txt:
       result = SignatureStatus.SIGNED
    elif 'voided' in status_txt:
       result = SignatureStatus.VOIDED

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
def send_contract_for_signature(session_id):

    app.logger.info('Executing send contract for signature')

    try:
        t_params = {}

        session = DocusignSession.query.filter_by(id=session_id).first()
        if session is None:
            raise ValueError("Session not present, session id is not valid")
        # Plan info
        credit_plan = CreditPaymentPlan.query.filter_by(name='Universal').first()
        if credit_plan is None:
            session.state = SessionState.FAILED
            db.session.commit()
            raise ValueError("CreditPaymentPlan entry is not present")

        # client and template checks are done in service
        client_id = session.client_id
        ds_tmpl_id = session.template.ds_key

        # fetch the lead object from the db
        client = Client.query.filter_by(id=client_id).first()
        # if client is not valid after session is created
        if client is None or (client.bank_account is None):
            session.state = SessionState.FAILED
            db.session.commit()
            raise ValueError("Client is not valid")

        # bank account
        bank_account = client.bank_account
        # payment contract
        payment_contract = client.payment_contract
        if payment_contract is None:
            session.state = SessionState.FAILED
            db.session.commit()
            raise ValueError("No payment contract found")

        # check if client has co-client associated with it
        co_sign = False
        if client.client_id is not None:
            co_sign = True
            cc_id = client.client_id

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
            t_params['AcctOwnerAddress'] = client_address.address1
            t_params['ClientCity'] = client_address.city
            t_params['AcctOwnerCity'] = client_address.city
            t_params['ClientState'] = client_address.state
            t_params['AcctOwnerState'] = client_address.state
            t_params['ClientZip'] = client_address.zip_code 
            t_params['AcctOwnerZip'] = client_address.zip_code
        else:
            t_params['ClientAddress'] = ''
            t_params['AcctOwnerAddress'] = ''
            t_params['ClientCity'] = ''
            t_params['AcctOwnerCity'] = ''
            t_params['ClientState'] = ''
            t_params['AcctOwnerState'] = ''
            t_params['ClientZip'] = ''
            t_params['AcctOwnerZip'] = ''

        t_params['AcctOwnerSSN'] =  client.ssn if client.ssn is not None else ""
        t_params['BankName'] =  client.bank_account.name
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

        ## Credit report table
        # fetch the credit report account 
        credit_account = client.credit_report_account
        if credit_account is None:
            session.state = SessionState.FAILED
            db.session.commit()
            raise ValueError("Credit account is not available")    

        credit_data = CreditReportData.query.filter_by(account_id=credit_account.id).all() 
        if credit_data is None or (len(credit_data) == 0): 
            session.state = SessionState.FAILED
            db.session.commit()
            raise ValueError("Credit data is not present")

        n = 0
        total = 0
        for record in credit_data:
            n = n + 1
            total = total + float(record.balance_original)

            t_params['Item{}'.format(n)] = str(n)
            t_params['Creditor{}'.format(n)] = record.creditor
            t_params['AccountNumber{}'.format(n)] = record.account_number
            t_params['BalanceOriginal{}'.format(n)] = record.balance_original
        # total
        t_params['PushTotal'] = "${:.2f}".format(total)

        # Repayment calculations
        total_debt = total
        debt_enrolled_percent = credit_plan.enrolled_percent
        credit_monitoring_fee = credit_plan.monitoring_fee_1signer
        if co_sign is True:
            credit_monitoring_fee = credit_plan.monitoring_fee_2signer
        monthly_bank_fee = credit_plan.monthly_bank_fee
        pymt_term = payment_contract.term
        min_allowed_fee = credit_plan.minimum_fee

        total_fee = (total_debt * (debt_enrolled_percent/100)) + (credit_monitoring_fee * pymt_term) + (monthly_bank_fee *pymt_term) 
        total_fee = round(total_fee, 2)
        if total_fee < min_allowed_fee:
            total_fee = min_allowed_fee

        monthly_fee = round((total_fee / pymt_term), 2)
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

        # Bank fee - currently hardcoded 
        t_params['BankFee1'] = "${:.2f}".format(credit_monitoring_fee)
        if co_sign is True:
            cc = Client.query.filter_by(id=cc_id).first()
            if cc is None:
                session.state = SessionState.FAILED
                db.session.commit()
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
        signature = DocusignSignature(envelope_id=key,
                                      status=SignatureStatus.SENT,
                                      modified=datetime.utcnow(),
                                      session_id=session.id)
        db.session.add(signature)
        db.session.commit()

        disp = ClientDisposition.query.filter_by(value='Contract Sent').first()
        client.disposition = disp
        db.session.commit()

    except Exception as err:
        print("Error in sending contract {}".format(str(err))) 

def send_modify_debts_for_signature(session_id):
    try:
        app.logger.info('Send Modify Debts  for signature')

        t_params = {}

        # fees related, fetch the common plan        
        credit_plan = CreditPaymentPlan.query.filter_by(name='Universal').first()
        if credit_plan is None:
            raise ValueError("CreditPaymentPlan entry is not present")

        session = DocusignSession.query.filter_by(id=session_id).first()
        if session is None:
            raise ValueError("Session is not present, session id is not valid")
        client_id = session.client_id
        ds_tmpl_id = session.template.ds_key

        # fetch the client from db
        client = Client.query.filter_by(id=client_id).first()
        # check if client has co-client associated with it
        co_sign = False
        if client.client_id is not None:
            co_sign = True
            cc_id = client.client_id

        client_full_name = '{} {}'.format(client.first_name, client.last_name)
        t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['ClientFullName'] = client_full_name
        t_params['ClientFullName1'] = client_full_name

        ## Credit report table
        # fetch the credit report account
        credit_account = client.credit_report_account
        credit_data    = CreditReportData.query.filter_by(account_id=credit_account.id).all()

        n = 0
        total = 0
        for record in credit_data:
            n = n + 1
            total = total + float(record.balance_original)

            t_params['Creditor{}'.format(n)] = record.creditor
            t_params['AccountNumber{}'.format(n)] = record.account_number
            t_params['BalanceOriginal{}'.format(n)] = record.balance_original
        # total
        t_params['PushTotal'] = "${:.2f}".format(total)

        # Repayment calculations
        total_debt = total
        debt_enrolled_percent = credit_plan.enrolled_percent
        credit_monitoring_fee = credit_plan.monitoring_fee_1signer
        if co_sign is True:
            credit_monitoring_fee = credit_plan.monitoring_fee_2signer
        monthly_bank_fee = credit_plan.monthly_bank_fee
        pymt_term = credit_account.term
        # min_allowed_fee = credit_plan.minimum_fee  

        total_fee = (total_debt * (debt_enrolled_percent/100)) + (credit_monitoring_fee * pymt_term) + (monthly_bank_fee *pymt_term)
        total_fee = round(total_fee, 2)
        monthly_fee = round((total_fee / pymt_term), 2)
        savings_amount = monthly_fee

        t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
        pymt_start = credit_account.payment_start_date
        start = pymt_start
        for i in range(0, pymt_term):
            index = i + 1
            t_params['SavingsAmount{}'.format(index)] = "${:.2f}".format(savings_amount)
            t_params['ProjectedDate{}'.format(index)] = start.strftime("%m/%d/%Y") 
            start = start + relativedelta(months=1)
            
        t_params['TotalSavingsAmount'] = "${:.2f}".format(total_fee)
        t_params['BankFee1'] = credit_monitoring_fee
        if co_sign is True:
            cc = Client.query.filter_by(id=cc_id).first()
            co_client_fname = '{} {}'.format(cc.first_name, cc.last_name)
            t_params['CoClientFullName'] = co_client_fname
            t_params['CoClientFullName1'] = co_client_fname
        
        ds = DocuSign()
        ds.authorize()

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
        signature = DocusignSignature(envelope_id=key,
                                      status=SignatureStatus.SENT,
                                      modified=datetime.utcnow(),
                                      session_id=session.id)

        db.session.add(signature)
        db.session.commit()

        # add client disposition

    except Exception:
        print("Error in send modify debts")


## Debts Removal
#removal_debts1_id = '2f48fe0c-c39e-4f64-a0a2-60b0f64c4fed'
#removal_debts2_id = '845cfdc3-5a29-45e4-a343-0ff71faaa0fb'
## Term Change
#term_change1_id = '9f12ec63-484c-4d84-ad73-5aa33455e827'
#term_change2_id = '79823547-1df0-475b-a109-235430b42821'
##Receive Summon
#receive_summon1_id = '711bd135-952e-4c7c-9ad5-af8039c9402b'
#receive_summon2_id = '912e322f-0023-4d68-b844-0b9c317f973f'
#
#additional_debts1_id = 'f5968884-ea09-4555-97bd-a46b2965a493' 
#additional_debts2_id = '8d121a9f-d34d-489b-ae14-43156fa34e5f'
#
#def send_removal_debts_for_signature(client_id,
#                                     cc_id,
#                                     co_sign=False,
#                                     savings_amount=688.20,
#                                     num_savings=30):
#    t_params = {}
#
#    ds = DocuSign()
#    ds.authorize()
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
#    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
#    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
#    tid = removal_debts1_id
#    if co_sign is True:
#        cc = Client.query.filter_by(id=cc_id).first()
#        tid = removal_debts2_id
#        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
#        t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
#        t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
#
#    key = ds.request_signature(template_id=tid,
#                               signer_name="{} {}".format(client.first_name, client.last_name),
#                               signer_email=client.email,
#                               template_params=t_params)
#
#
#def send_term_change_for_signature(client_id,
#                                   cc_id,
#                                   co_sign=False,
#                                   savings_amount=688.20,
#                                   num_savings=30):
#
#    t_params = {}
#
#    ds = DocuSign()
#    ds.authorize()
#    if co_sign is True:
#        tid = term_change2_id
#    else:
#        tid = term_change1_id
#
#    # fetch the client from db
#    client = Client.query.filter_by(id=client_id).first()
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
#def send_additional_debts_for_signature(client_id,
#                                        cc_id,
#                                        co_sign=False,
#                                        savings_amount=688.20,
#                                        num_savings=30):
#
#    t_params = {}
#
#    ds = DocuSign()
#    ds.authorize()
#    if co_sign is True:
#        tid = additional_debts2_id
#    else:
#        tid = additional_debts1_id
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
#
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

