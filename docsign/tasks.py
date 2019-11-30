from app.main import db
from .docusign import DocuSign
from .models import DocusignTemplate 
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


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

# worker task 
# send template for signing
def send_template_for_signing(client_id, template_id, template_params):
    try:
        client = Client.query.filter_by(id=client_id).first()
        if client is None:
            raise ValueError('Client not found')

        tmpl = DocusignTemplate.query.filter_by(id=template_id).first() 
        if tmpl is None:
            raise ValueError('Template not found')

        ds = DocuSign()
        ds.authorize()
        env_id = ds.request_signature(tmpl.ds_key, 
                                      client.first_name, 
                                      client.email,
                                      template_params=template_params)        
        # create a database entry
        signature = DocusignSignature(envelope_id=env_id,
                                      status=SignatureStatus.SENT,
                                      client_id=client_id,
                                      template_id=template_id)
        db.session.add(signature)
        db.session.commit()

    except Exception as err:
        print("send template for signing task {}".format(str(err)))


# task
# update signature status
def update_signature_status():
    try:
        ds = DocuSign()
        ds.authorize()

        signatures = DocusignSignature.query.filter_by(status=SignatureStatus.SENT).all()
        for signature in signatures:
            status = ds.envelope_status(signature.envelope_id)    

            if status.lower() != SignatureStatus.SENT.name.lower():
                # update database
                signature.status = _to_status(status)
                db.session.commit()


    except Exception as err:
        print("Update signature status {}".format(str(err)))


def _to_status(status_txt):
    status_txt = status_txt.lower()
    result = SignatureStatus.CREATED 
    if 'sent' in  status_txt:
        result = SignatureStatus.SENT
    elif 'signed' in status_txt:
       result = SignatureStatus.SIGNED
    elif 'created' in status_txt:
       result = SignatureStatus.Created
    elif 'delivered' in status_txt:
       result = SignatureStatus.DELIVERED
    elif 'voided' in status_txt:
       result = SignatureStatus.VOIDED

    return result

# EDMS contract template
# Signer1 & Signer2 
_test_contract_params = {
    'CurrentDate': datetime.now().strftime("%m/%d/%Y"),
    'ClientFirstName': 'John',
    'ClientLastName':  'Smith',
    'ClientAddress': '1234 Coder Way',
    'ClientCity': 'San Diego',
    'ClientState': 'Ca',
    'ClientZip': '92111',
    'ClientHomePhone': '1234567890',
    'ClientWorkPhone': '2345678910',
    'ClientMobilePhone': '3456789012',
    'ClientEmail': 'Yoda@gmail.com',
    'ClientDOB': '1/1/1973',
    'ClientLast4SSN': '1234',
    'CoClientFirstName': 'Melaine',
    'CoClientLastName': 'Johnson',
    'CoClientAddress': '5678 CRM Avenue',
    'CoClientCity': 'San Francisco',
    'CoClientState': 'CA',
    'CoClientZip': '92456',
    'CoClientHomePhone': '4567890123',
    'CoClientWorkPhone': '5678901234',
    'CoClientMobilePhone': '6789012345',
    'CoClientEmail': 'PrincessLeah@gmail.com',
    'CoClientDOB': '2/1/1988',
    'CoClientLast4SSN': '4567',
    'Item1': '1',
    'Item2': '2',
    'Item3': '3',
    'Item4': '4',
    'Item5': '5',
    'Item6': '6',
    'Item7': '7',
    'Item8': '8',
    'Item9': '9',
    'Item10': '10',
    'Item11': '11',
    'Item12': '12',
    'Item13': '13',
    'Item14': '14',
    'Item15': '15',
    'Item16': '16',
    'Item17': '17',
    'Item18': '18',
    'Item19': '19',
    'Item20': '20',
    'Item21': '21',
    'Item22': '22',
    'Item23': '23',
    'Item24': '24',
    'Item25': '25',
    'Item26': '26',
    'Item27': '27',
    'Item28': '28',
    'Item29': '29',
    'Item30': '30',
    'Creditor1': 'Bank of America',
    'Creditor2': 'Citibank',
    'Creditor3': 'Wells Fargo',
    'Creditor4': 'Discover',
    'Creditor5': 'Chase',
    'Creditor6': 'USAA',
    'Creditor7': 'American Express',
    'Creditor8': 'Bank of America',
    'Creditor9': 'Citibank',
    'Creditor10': 'Wells Fargo',
    'Creditor11': 'Discover',
    'Creditor12': 'Chase',
    'Creditor13': 'USAA',
    'Creditor14': 'American Express',
    'Creditor15': 'Bank of America',
    'Creditor16': 'Citibank',
    'Creditor17': 'Wells Fargo',
    'Creditor18': 'Discover',
    'Creditor19': 'Chase',
    'Creditor20': 'USAA',
    'Creditor21': 'American Express',
    'Creditor22': 'Bank of America',
    'Creditor23': 'Citibank',
    'Creditor24': 'Wells Fargo',
    'Creditor25': 'Discover',
    'Creditor26': 'Chase',
    'Creditor27': 'USAA',
    'Creditor28': 'American Express',
    'Creditor29': 'Bank of America',
    'Creditor30': 'Citibank',
    'AccountNumber1': '1234567890',
    'AccountNumber2': '2345678901',
    'AccountNumber3': '3456789012',
    'AccountNumber4': '4567890123',
    'AccountNumber5': '5678901234',
    'AccountNumber6': '6789012345',
    'AccountNumber7': '7890123456',
    'AccountNumber8': '8901234567',
    'AccountNumber9': '9012345678',
    'AccountNumber10': '10697302239',
    'AccountNumber11': '11728395060',
    'AccountNumber12': '12759487881',
    'AccountNumber13': '13790580702',
    'AccountNumber14': '14821673523',
    'AccountNumber15': '15852766344',
    'AccountNumber16': '16883859165',
    'AccountNumber17': '17914951986',
    'AccountNumber18': '18946044807',
    'AccountNumber19': '19977137628',
    'AccountNumber20': '21008230449',
    'AccountNumber21': '22039323270',
    'AccountNumber22': '23070416091',
    'AccountNumber23': '24101508912',
    'AccountNumber24': '25132601733',
    'AccountNumber25': '26163694554',
    'AccountNumber26': '27194787375',
    'AccountNumber27': '28225880196',
    'AccountNumber28': '29256973017',
    'AccountNumber29': '30288065838',
    'AccountNumber30': '31319158659',
    'BalanceOriginal1': '$111.00',
    'BalanceOriginal2': '$222.00',
    'BalanceOriginal3': '$333.00',
    'BalanceOriginal4': '$444.00',
    'BalanceOriginal5': '$555.00',
    'BalanceOriginal6': '$666.00',
    'BalanceOriginal7': '$777.00',
    'BalanceOriginal8': '$888.00',
    'BalanceOriginal9': '$999.00',
    'BalanceOriginal10': '$1,110.00',
    'BalanceOriginal11': '$1,221.00',
    'BalanceOriginal12': '$1,332.00',
    'BalanceOriginal13': '$1,443.00',
    'BalanceOriginal14': '$1,554.00',
    'BalanceOriginal15': '$1,665.00',
    'BalanceOriginal16': '$1,776.00',
    'BalanceOriginal17': '$1,887.00',
    'BalanceOriginal18': '$1,998.00',
    'BalanceOriginal19': '$2,109.00',
    'BalanceOriginal20': '$2,220.00',
    'BalanceOriginal21': '$2,331.00',
    'BalanceOriginal22': '$2,442.00',
    'BalanceOriginal23': '$2,553.00',
    'BalanceOriginal24': '$2,664.00',
    'BalanceOriginal25': '$2,775.00',
    'BalanceOriginal26': '$2,886.00',
    'BalanceOriginal27': '$2,997.00',
    'BalanceOriginal28': '$3,108.00',
    'BalanceOriginal29': '$3,219.00',
    'BalanceOriginal30': '$3,330.00',
    'PushTotal': '$51,615.00',
    'paymentNumber1': '1',
    'paymentNumber2': '2',
    'paymentNumber3': '3',
    'paymentNumber4': '4',
    'paymentNumber5': '5',
    'paymentNumber6': '6',
    'paymentNumber7': '7',
    'paymentNumber8': '8',
    'paymentNumber9': '9',
    'paymentNumber10': '10',
    'paymentNumber11': '11',
    'paymentNumber12': '12',
    'paymentNumber13': '13',
    'paymentNumber14': '14',
    'paymentNumber15': '15',
    'paymentNumber16': '16',
    'paymentNumber17': '17',
    'paymentNumber18': '18',
    'paymentNumber19': '19',
    'paymentNumber21': '21',
    'paymentNumber22': '22',
    'paymentNumber23': '23',
    'paymentNumber24': '24',
    'paymentNumber25': '25',
    'paymentNumber26': '26',
    'paymentNumber27': '27',
    'paymentNumber28': '28',
    'paymentNumber29': '29',
    'paymentNumber30': '30',
    'ProjectedDate1': '12/15/2019',
    'ProjectedDate2': '1/15/2020',
    'ProjectedDate3': '2/15/2020',
    'ProjectedDate4': '3/15/2020',
    'ProjectedDate5': '4/15/2020',
    'ProjectedDate6': '5/15/2020',
    'ProjectedDate7': '6/15/2020',
    'ProjectedDate8': '7/15/2020',
    'ProjectedDate9': '8/15/2020',
    'ProjectedDate10': '9/15/2020',
    'ProjectedDate11': '10/15/2020',
    'ProjectedDate12': '11/15/2020',
    'ProjectedDate13': '12/15/2020',
    'ProjectedDate14': '1/15/2021',
    'ProjectedDate15': '2/15/2021',
    'ProjectedDate16': '3/15/2021',
    'ProjectedDate17': '4/15/2021',
    'ProjectedDate18': '5/15/2021',
    'ProjectedDate19': '6/15/2021',
    'ProjectedDate20': '7/15/2021',
    'ProjectedDate21': '8/15/2021',
    'ProjectedDate22': '9/15/2021',
    'ProjectedDate23': '10/15/2021',
    'ProjectedDate24': '11/15/2021',
    'ProjectedDate25': '12/15/2021',
    'ProjectedDate26': '1/15/2022',
    'ProjectedDate27': '2/15/2022',
    'ProjectedDate28': '3/15/2022',
    'ProjectedDate29': '4/15/2022',
    'ProjectedDate30': '5/15/2022',
    'SavingsAmount1': '$688.20',
    'SavingsAmount2': '$688.20',
    'SavingsAmount3': '$688.20',
    'SavingsAmount4': '$688.20',
    'SavingsAmount5': '$688.20',
    'SavingsAmount6': '$688.20',
    'SavingsAmount7': '$688.20',
    'SavingsAmount8': '$688.20',
    'SavingsAmount9': '$688.20',
    'SavingsAmount10': '$688.20',
    'SavingsAmount11': '$688.20',
    'SavingsAmount12': '$688.20',
    'SavingsAmount13': '$688.20',
    'SavingsAmount14': '$688.20',
    'SavingsAmount15': '$688.20',
    'SavingsAmount16': '$688.20',
    'SavingsAmount17': '$688.20',
    'SavingsAmount18': '$688.20',
    'SavingsAmount19': '$688.20',
    'SavingsAmount20': '$688.20',
    'SavingsAmount21': '$688.20',
    'SavingsAmount22': '$688.20',
    'SavingsAmount23': '$688.20',
    'SavingsAmount24': '$688.20',
    'SavingsAmount25': '$688.20',
    'SavingsAmount26': '$688.20',
    'SavingsAmount27': '$688.20',
    'SavingsAmount28': '$688.20',
    'SavingsAmount29': '$688.20',
    'SavingsAmount30': '$688.20',
    'TotalSavingsAmount': '$20,646.00',
    'AcctOwnerName': 'John Smith',
    'AcctOwnerSSN': '1234',
    'AcctOwnerDOB': '1/1/1973',
    'AcctOwnerAddress': '1234 Coder Way',
    'AcctOwnerCity': 'San Diego',
    'AcctOwnerState': 'Ca',
    'AcctOwnerZip': '92111',
    'AcctOwnerMobile': '3456789012',
    'BankName': 'Bank Of America',
    'BankRoutingNbr': '12345678',
    'BankAccountNbr': '9876543210',
    'InvoiceAmount': '$20,646.00',
    '1stPaymentDate10': '12/15/2019',
    '1stPaymentDate': '12/15/2019',
    'BankAccountType': 'Checking',
    'CurrentDate100': datetime.now().strftime("%m/%d/%Y"),
    'CurrentDate2': datetime.now().strftime("%m/%d/%Y"),
    'InvoiceAmount1': '$20,646.00',
    'SavingsAmount42': '$688.20',
    'Term3': '30',
    'BankFee1': '$89',
    'Term1': '30',
    'ClientFullName1': 'John Smith',
    'CoClientFullName1': 'Melanie Johnson',
    'ClientFullName2': 'John Smith',
    'CoClientFullName2': 'Melanie Johnson',
    'CurrentDate101': datetime.now().strftime("%m/%d/%Y"),
    'CurrentDate102': datetime.now().strftime("%m/%d/%Y"),
    'CurrentDate3': datetime.now().strftime("%m/%d/%Y"),
    '7businessdaysafterCurrentDate': (datetime.now() +timedelta(days=7)).strftime("%m/%d/%Y"),
}

elite_dms_contract1_signed = '5ac45a69-e135-4ff3-8547-67abf0d50b3a'
elite_dms_contract2_signed = 'ffb8ec43-3574-4343-a140-ccd7c6807d2f'

# test routines
def send_contract_for_signature(name, email, co_sign=False):
    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = elite_dms_contract2_signed
    else:
        tid = elite_dms_contract1_signed
    key = ds.request_signature(template_id=tid,
                               signer_name=name,
                               signer_email=email,
                               template_params=_test_contract_params)

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

def send_removal_debts_for_signature(first_name, 
                                     last_name,
                                     email, 
                                     savings_amount=688.20,
                                     num_savings=30,
                                     co_sign=False,
                                     co_first_name = 'Melanie',
                                     co_last_name = 'Johnson'):
    t_params = {}

    ds = DocuSign()
    ds.authorize()

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
    t_params['ClientFullName'] = "{} {}".format(first_name, last_name)
    t_params['ClientFullName1'] = "{} {}".format(first_name, last_name)
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
        tid = removal_debts2_id
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(co_first_name, co_last_name)
        t_params['CoClientFullName1'] = "{} {}".format(co_first_name, co_last_name)

    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(first_name, last_name),
                               signer_email=email,
                               template_params=t_params)


def send_term_change_for_signature(first_name,
                                   last_name, 
                                   email, 
                                   savings_amount=688.20,
                                   num_savings=30,
                                   co_sign=False,
                                   co_first_name = 'Melanie',
                                   co_last_name = 'Johnson'):

    t_params = {}

    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = term_change2_id
    else:
        tid = term_change1_id

    t_params['CurrentDate'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate100'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['CurrentDate101'] = datetime.now().strftime("%m/%d/%Y")  
    t_params['ClientFullName'] = "{} {}".format(first_name, last_name)
    t_params['ClientFullName1'] = "{} {}".format(first_name, last_name)
    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
        
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    if co_sign is True:
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(co_first_name, co_last_name)
        t_params['CoClientFullName1'] = "{} {}".format(co_first_name, co_last_name)
    
    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(first_name, last_name),
                               signer_email=email,
                               template_params=t_params)


def send_receive_summon_for_signature(first_name,
                                   last_name, 
                                   email, 
                                   savings_amount=688.20,
                                   num_savings=30,
                                   co_sign=False,
                                   co_first_name = 'Melanie',
                                   co_last_name = 'Johnson'):

    t_params = {}

    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = receive_summon2_id
    else:
        tid = receive_summon1_id

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
    t_params['ClientFullName'] = "{} {}".format(first_name, last_name)
    t_params['ClientFullName1'] = "{} {}".format(first_name, last_name)
    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
        
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    if co_sign is True:
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(co_first_name, co_last_name)
        t_params['CoClientFullName1'] = "{} {}".format(co_first_name, co_last_name)
    
    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(first_name, last_name),
                               signer_email=email,
                               template_params=t_params)

def send_additional_debts_for_signature(first_name,
                                   last_name, 
                                   email, 
                                   savings_amount=688.20,
                                   num_savings=30,
                                   co_sign=False,
                                   co_first_name = 'Melanie',
                                   co_last_name = 'Johnson'):

    t_params = {}

    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = additional_debts2_id
    else:
        tid = additional_debts1_id

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
    t_params['ClientFullName'] = "{} {}".format(first_name, last_name)
    t_params['ClientFullName1'] = "{} {}".format(first_name, last_name)

    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
        
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    if co_sign is True:
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(co_first_name, co_last_name)
        t_params['CoClientFullName1'] = "{} {}".format(co_first_name, co_last_name)
    
    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(first_name, last_name),
                               signer_email=email,
                               template_params=t_params)


def send_modify_debts_for_signature(first_name,
                                   last_name,
                                   email,
                                   savings_amount=688.20,
                                   num_savings=30,
                                   co_sign=False,
                                   co_first_name = 'Melanie',
                                   co_last_name = 'Johnson'):

    t_params = {}

    ds = DocuSign()
    ds.authorize()
    if co_sign is True:
        tid = modify_debts2_id
    else:
        tid = modify_debts1_id

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
    t_params['ClientFullName'] = "{} {}".format(first_name, last_name)
    t_params['ClientFullName1'] = "{} {}".format(first_name, last_name)

    t_params['SavingsAmount'] = "${:.2f}".format(savings_amount)
    start = datetime(2019, 12, 15)
    for i in range(1,31):
        t_params['SavingsAmount{}'.format(i)] = "${:.2f}".format(savings_amount)
        t_params['ProjectedDate{}'.format(i)] = start.strftime("%m/%d/%Y") 
        start = start + relativedelta(months=1)
        
    t_params['TotalSavingsAmount'] = "${:.2f}".format(num_savings*savings_amount)
    t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_1SIGNER)
    if co_sign is True:
        t_params['BankFee1'] = "${:.2f}".format(BANKFEE_FOR_2SIGNER)
        t_params['CoClientFullName'] = "{} {}".format(co_first_name, co_last_name)
        t_params['CoClientFullName1'] = "{} {}".format(co_first_name, co_last_name)
    
    key = ds.request_signature(template_id=tid,
                               signer_name="{} {}".format(first_name, last_name),
                               signer_email=email,
                               template_params=t_params)
