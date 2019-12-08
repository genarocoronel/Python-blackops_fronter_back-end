from app.main import db
from app.main.service.docusign_service import DocuSign
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.main.model.client import Client
from app.main.model.docsign import *

from flask import current_app as app


BANKFEE_FOR_1SIGNER = 59.00
BANKFEE_FOR_2SIGNER = 89.00

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
            print(session.id)
            print(session.state)
            signatures = session.signatures
            completed = True 
            for signature in signatures:
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
                   
                signature.status = status
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


_credit_data0 = [
    ['Bank of America', '1234567890', 111],
    ['Citibank', '2345678901', 222],
    ['Wells Fargo', '3456789012', 333],
    ['Discover', '4567890123', 444],
    ['Chase', '5678901234', 555],
    ['USAA', '6789012345', 666],
    ['American Express', '7890123456', 777],
    ['Bank of America', '8901234567', 888],
    ['Citibank', '9012345678', 999],
    ['Wells Fargo', '10697302239', 1110],
    ['Discover', '11728395060', 1221],
    ['Chase', '12759487881', 1332],
    ['USAA', '13790580702', 1443],
    ['American Express', '14821673523', 1554],
    ['Bank of America', '15852766344', 1665],
    ['Citibank', '16883859165', 1776],
    ['Wells Fargo', '17914951986', 1887],
    ['Discover', '18946044807', 1998],
    ['Chase', '19977137628', 2109],
    ['USAA', '21008230449', 2220],
    ['American Express', '22039323270', 2331],
    ['Bank of America', '23070416091', 2442],
    ['Citibank', '24101508912', 2553],
    ['Wells Fargo', '25132601733', 2664],
    ['Discover', '26163694554', 2775],
    ['Chase', '27194787375', 2886],
    ['USAA', '28225880196', 2997],
    ['American Express', '29256973017', 3108],
    ['Bank of America', '30288065838', 3219],
    ['Citibank', '31319158659', 3330],
]

SAVINGS_TERM = 30
SAVINGS_AMOUNT = 688.20

# test routines
def send_contract_for_signature(session_id):

    app.logger.info('Executing send contract for signature')

    try:
        t_params = {}

        session = DocusignSession.query.filter_by(id=session_id).first()
        client_id = session.client_id
        co_sign   = session.cosign_required
        ds_tmpl_id = session.template.ds_key

        num_savings = SAVINGS_TERM
        savings_amount = SAVINGS_AMOUNT

        # fetch the lead object from the db
        client = Client.query.filter_by(id=client_id).first()
        # check if client has co-client associated with it
        print("here 2")
        
        ## testing
        ## remove it
        if co_sign is True:
            cc_id = 3 

        client_full_name = '{} {}'.format(client.first_name, client.last_name)
        t_params['ClientFirstName'] = client.first_name
        t_params['ClientLastName'] = client.last_name 
        t_params['ClientAddress'] = client.address 
        t_params['AcctOwnerAddress'] = client.address
        t_params['ClientCity'] = client.city
        t_params['AcctOwnerCity'] = client.city
        t_params['ClientState'] = client.state
        t_params['AcctOwnerState'] = client.state
        t_params['ClientZip'] = client.zip 
        t_params['AcctOwnerZip'] = client.zip
        t_params['ClientHomePhone'] = client.phone
        t_params['ClientWorkPhone'] = client.phone
        t_params['ClientMobilePhone'] = client.phone
        t_params['AcctOwnerMobile'] = client.phone
        t_params['ClientEmail'] = client.email
        t_params['ClientDOB'] = '1/1/1973'
        t_params['AcctOwnerDOB'] = '1/1/1973'
        t_params['ClientLast4SSN'] = '2341'
        t_params['AcctOwnerName'] = client_full_name
        t_params['ClientFullName1'] = client_full_name
        t_params['ClientFullName2'] = client_full_name

        t_params['AcctOwnerSSN'] =  '2341'
        t_params['BankName'] =  client.bank_account.name
        t_params['BankRoutingNbr'] =  client.bank_account.routing_number
        t_params['BankAccountNbr'] = client.bank_account.account_number
        t_params['BankAccountType'] = client.bank_account.type.value

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

        ## dummy values using API parameter
        ## need to obtain this from database
        t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
        t_params['SavingsAmount42'] = "${:.2f}".format(savings_amount)
        start = datetime(2019, 12, 15)
        t_params['1stPaymentDate'] = start.strftime("%m/%d/%Y")
        t_params['1stPaymentDate10'] = start.strftime("%m/%d/%Y")
        for i in range(1,31):
            t_params['paymentNumber{}'.format(i)] = str(i)
            t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
            t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
            start = start + relativedelta(months=1)
        t_params['Term1'] = str(num_savings)
        t_params['Term3'] = str(num_savings)
        t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
        t_params['InvoiceAmount'] = "${:.2f}".format(num_savings*savings_amount)
        t_params['InvoiceAmount1'] = "${:.2f}".format(num_savings*savings_amount)

        ## Credit report table
        n = 0
        total = 0
        for c in _credit_data0:
            n = n + 1
            total = total + c[2]
            t_params['Item{}'.format(n)] = str(n)
            t_params['Creditor{}'.format(n)] = c[0]
            t_params['AccountNumber{}'.format(n)] = c[1]
            t_params['BalanceOriginal{}'.format(n)] = "${:.2f}".format(c[2])
        # total
        t_params['PushTotal'] = "${:.2f}".format(total)

        # Bank fee - currently hardcoded 
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
        if co_sign is True:
            cc = Client.query.filter_by(id=cc_id).first()
            co_client_fname = '{} {}'.format(cc.first_name, cc.last_name)
            t_params['CoClientFirstName'] = cc.first_name
            t_params['CoClientLastName'] = cc.last_name
            t_params['CoClientAddress'] = cc.address
            t_params['CoClientCity'] = cc.city
            t_params['CoClientState'] = cc.state
            t_params['CoClientZip'] = cc.zip
            t_params['CoClientHomePhone'] = cc.phone
            t_params['CoClientWorkPhone'] = cc.phone
            t_params['CoClientMobilePhone'] = cc.phone
            t_params['CoClientEmail'] = cc.email
            t_params['CoClientDOB'] = '2/1/1988'
            t_params['CoClientLast4SSN'] = '4567'
            t_params['CoClientFullName'] = co_client_fname
            t_params['CoClientFullName1'] = co_client_fname
            t_params['CoClientFullName2'] = co_client_fname

            t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)

        #Docusign interface
        ds = DocuSign()
        ds.authorize()

        # Send to primary client
        key = ds.request_signature(template_id=ds_tmpl_id,
                                   signer_name=client_full_name,
                                   signer_email=client.email,
                                   template_params=t_params)
       

        # create signatures
        signature = DocusignSignature(envelope_id=key,
                                      status=SignatureStatus.SENT,
                                      client_id=client.id,
                                      modified=datetime.utcnow(),
                                      is_primary=True,
                                      session_id=session.id)
        db.session.add(signature)
        db.session.commit()
        # if co-sign, Create a draft for the co-client 
        if co_sign is True:
            co_env_id = ds.request_signature(template_id=ds_tmpl_id,
                                             signer_name=co_client_fname,
                                             signer_email=cc.email,
                                             is_primary=False,
                                             template_params=t_params)

            signature = DocusignSignature(envelope_id=co_env_id,
                                          status=SignatureStatus.SENT,
                                          client_id=cc.id,
                                          modified=datetime.utcnow(),
                                          is_primary=False,
                                          session_id=session.id)
            db.session.add(signature)
            db.session.commit()

    except Exception as err:
        print("Error in sending contract {}".format(str(err))) 

# Debts Removal
removal_debts1_id = '2f48fe0c-c39e-4f64-a0a2-60b0f64c4fed'
removal_debts2_id = '845cfdc3-5a29-45e4-a343-0ff71faaa0fb'
# Term Change
term_change1_id = '9f12ec63-484c-4d84-ad73-5aa33455e827'
term_change2_id = '79823547-1df0-475b-a109-235430b42821'
#Receive Summon
receive_summon1_id = '711bd135-952e-4c7c-9ad5-af8039c9402b'
receive_summon2_id = '912e322f-0023-4d68-b844-0b9c317f973f'

additional_debts1_id = 'f5968884-ea09-4555-97bd-a46b2965a493' 
additional_debts2_id = '8d121a9f-d34d-489b-ae14-43156fa34e5f'

modify_debts1_id = '6f7fe7ff-1407-4772-acc0-fd969c91b47a'
modify_debts2_id = '12af2e6f-c1ce-4100-9dce-5a18a820a353'


_credit_data = [
    ['Bank of America', '1234567890', 111],
    ['Citibank', '2345678901', 222],
    ['Wells Fargo', '3456789012', 333],
    ['Discover', '4567890123', 444],
    ['Chase', '5678901234', 555],
    ['USAA', '6789012345', 666],
    ['American Express', '7890123456', 777],
    ['Bank of America', '8901234567', 888],
    ['Citibank', '9012345678', 999],
    ['Wells Fargo', '10697302239', 1110],
    ['Discover', '11728395060', 1221],
    ['Chase', '12759487881', 1332],
    ['USAA', '13790580702', 1443],
    ['American Express', '14821673523', 1554],
    ['Bank of America', '15852766344', 1665],
    ['Citibank', '16883859165', 1776],
    ['Wells Fargo', '17914951986', 1887],
    ['Discover', '18946044807', 1998],
    ['Chase', '19977137628', 2109],

]

def send_modify_debts_for_signature(session_id):
    try:
        t_params = {}

        session = DocusignSession.query.filter_by(id=session_id).first()
        client_id = session.client_id
        co_sign   = session.cosign_required
        ds_tmpl_id = session.template.ds_key

        num_savings = SAVINGS_TERM
        savings_amount = SAVINGS_AMOUNT

        # fetch the client from db
        client = Client.query.filter_by(id=client_id).first()

        n = 0
        total = 0
        for c in _credit_data:
            n = n + 1
            total = total + c[2]
            t_params['Creditor{}'.format(n)] = c[0] 
            t_params['AccountNumber{}'.format(n)] = c[1] 
            t_params['BalanceOriginal{}'.format(n)] = "${:.2f}".format(c[2])

        n = n + 1
        total = total + 2200 
        t_params['Creditor{}'.format(n)] = 'USAA'
        t_params['AccountNumber{}'.format(n)] = '21977137628'
        t_params['BalanceOriginal{}'.format(n)] = "${:.2f}".format(2200)
   
        # total
        t_params['PushTotal'] = "${:.2f}".format(total)

        t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
        t_params['ClientFullName'] = "{} {}".format(client.first_name, client.last_name)
        t_params['ClientFullName1'] = "{} {}".format(client.first_name, client.last_name)

        t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
        start = datetime(2019, 12, 15)
        for i in range(1,31):
            t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
            t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
            start = start + relativedelta(months=1)
            
        t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
        if co_sign is True:
            cc = Client.query.filter_by(id=cc_id).first()
            co_client_fname = '{} {}'.format(cc.first_name, cc.last_name)
            t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
            t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
            t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
        
        ds = DocuSign()
        ds.authorize()

        key = ds.request_signature(template_id=ds_tmpl_id,
                                   signer_name="{} {}".format(client.first_name, client.last_name),
                                   signer_email=client.email,
                                   template_params=t_params)
        # create signatures
        signature = DocusignSignature(envelope_id=key,
                                      status=SignatureStatus.SENT,
                                      client_id=client.id,
                                      modified=datetime.utcnow(),
                                      is_primary=True,
                                      session_id=session.id)
        db.session.add(signature)
        db.session.commit()
        # if co-sign, Create a draft for the co-client 
        if co_sign is True:
            co_env_id = ds.request_signature(template_id=ds_tmpl_id,
                                             signer_name=co_client_fname,
                                             signer_email=cc.email,
                                             is_primary=False,
                                             template_params=t_params)

            signature = DocusignSignature(envelope_id=co_env_id,
                                          status=SignatureStatus.SENT,
                                          client_id=cc.id,
                                          modified=datetime.utcnow(),
                                          is_primary=False,
                                          session_id=session.id)
            db.session.add(signature)
            db.session.commit()

    except Exception:
        print("Error in send modify debts")

def send_removal_debts_for_signature(client_id,
                                     cc_id,
                                     co_sign=False,
                                     savings_amount=688.20,
                                     num_savings=30):
    t_params = {}

    ds = DocuSign()
    ds.authorize()

    # fetch the client from db
    client = Client.query.filter_by(id=client_id).first()

    n = 0
    total = 0
    for c in _credit_data:
        n = n + 1
        total = total + c[2]
        t_params['Creditor{}'.format(n)] = c[0] 
        t_params['AccountNumber{}'.format(n)] = c[1] 
        t_params['BalanceOriginal{}'.format(n)] = "${:.2f}".format(c[2])
    # total
    t_params['PushTotal'] = "${:.2f}".format(total)
        
    t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['ClientFullName'] = "{} {}".format(client.first_name, client.last_name)
    t_params['ClientFullName1'] = "{} {}".format(client.first_name, client.last_name)
    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    tid = removal_debts1_id
    if co_sign is True:
        cc = Client.query.filter_by(id=cc_id).first()
        tid = removal_debts2_id
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
        t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)

    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(client.first_name, client.last_name),
                               signer_email=client.email,
                               template_params=t_params)


def send_term_change_for_signature(client_id,
                                   cc_id,
                                   co_sign=False,
                                   savings_amount=688.20,
                                   num_savings=30):

    t_params = {}

    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = term_change2_id
    else:
        tid = term_change1_id

    # fetch the client from db
    client = Client.query.filter_by(id=client_id).first()

    t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['ClientFullName'] = "{} {}".format(client.first_name, client.last_name)
    t_params['ClientFullName1'] = "{} {}".format(client.first_name, client.last_name)
    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
        
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    if co_sign is True:
        cc = Client.query.filter_by(id=cc_id).first()
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
        t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
    
    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(client.first_name, client.last_name),
                               signer_email=client.email,
                               template_params=t_params)


def send_receive_summon_for_signature(client_id,
                                      cc_id,
                                      co_sign=False,
                                      savings_amount=688.20,
                                      num_savings=30):

    t_params = {}

    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = receive_summon2_id
    else:
        tid = receive_summon1_id

    # fetch the client from db
    client = Client.query.filter_by(id=client_id).first()

    n = 0
    total = 0
    for c in _credit_data:
        n = n + 1
        total = total + c[2]
        t_params['Creditor{}'.format(n)] = c[0] 
        t_params['AccountNumber{}'.format(n)] = c[1] 
        t_params['BalanceOriginal{}'.format(n)] = "${:.2f}".format(c[2])
    # total
    t_params['PushTotal'] = "${:.2f}".format(total)

    t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['ClientFullName'] = "{} {}".format(client.first_name, client.last_name)
    t_params['ClientFullName1'] = "{} {}".format(client.first_name, client.last_name)
    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
        
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    if co_sign is True:
        cc = Client.query.filter_by(id=cc_id).first()
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
        t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
    
    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(client.first_name, client.last_name),
                               signer_email=client.email,
                               template_params=t_params)

def send_additional_debts_for_signature(client_id,
                                        cc_id,
                                        co_sign=False,
                                        savings_amount=688.20,
                                        num_savings=30):

    t_params = {}

    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = additional_debts2_id
    else:
        tid = additional_debts1_id

    # fetch the client from db
    client = Client.query.filter_by(id=client_id).first()

    n = 0
    total = 0
    for c in _credit_data:
        n = n + 1
        total = total + c[2]
        t_params['Creditor{}'.format(n)] = c[0] 
        t_params['AccountNumber{}'.format(n)] = c[1] 
        t_params['BalanceOriginal{}'.format(n)] = "${:.2f}".format(c[2])
    # total
    t_params['PushTotal'] = "${:.2f}".format(total)

    t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['ClientFullName'] = "{} {}".format(client.first_name, client.last_name)
    t_params['ClientFullName1'] = "{} {}".format(client.first_name, client.last_name)

    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
        
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    if co_sign is True:
        cc = Client.query.filter_by(id=cc_id).first()
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(cc.first_name, cc.last_name)
        t_params['CoClientFullName1'] = "{} {}".format(cc.first_name, cc.last_name)
    
    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(client.first_name, client.last_name),
                               signer_email=client.email,
                               template_params=t_params)


