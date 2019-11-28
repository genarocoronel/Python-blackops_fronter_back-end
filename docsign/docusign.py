from docusign_esign import ApiClient, EnvelopeDefinition, TemplateRole, EnvelopesApi, Configuration, Recipients, Document, Signer, Recipients, TemplatesApi
import base64, os
from datetime import datetime, timedelta
import time

DS_ACCOUNT_ID = '910decab-18f3-4eae-8456-74552da97b03'

TOKEN_REPLACEMENT_IN_SECONDS = 10 * 60
TOKEN_EXPIRATION_IN_SECONDS = 3600

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

# Docsign object to interface with Docsign cloud service
class DocuSign(object):
    # Account Id
    _USER_ID = 'b5a198c8-d772-496f-bea2-f814e70f7fbd'
    _ACCOUNT_ID = '910decab-18f3-4eae-8456-74552da97b03'
    _INTEGRATION_KEY = 'a40df05f-4138-42c7-bae0-140a80b73baa'
    _BASE_PATH  = 'https://demo.docusign.net/restapi'
    _EMAIL_SUBJECT = 'Please sign this document from CRM Limited'
    
    # AUTH
    _DS_AUTH_HOST = 'account-d.docusign.com'

    def __init__(self):
        self._client = None
  
    # Generate access token using oAuth
    def authorize(self):
        self._client = ApiClient()
        # check the token details in the cache
        if self._check_token() is False:
            self._update_token()
        # set the access token in Authorization headers
        self._client.set_base_path(self._BASE_PATH)
        self._client.host = self._BASE_PATH
        self._client.set_default_header("Authorization", "Bearer " + self._access_token)
        return self._client

    def _check_token(self):
        return False
       
    def _update_token(self):
        client = self._client
        pk_bytes = None
        with open('docsign/rsa_private.key', mode='rb') as file: 
            pk_bytes = file.read()

        jwt_token = client.request_jwt_user_token(
                                             self._INTEGRATION_KEY,
                                             self._USER_ID,
                                             self._DS_AUTH_HOST,
                                             pk_bytes,
                                             TOKEN_EXPIRATION_IN_SECONDS
                                            )

        #jwt_token = client.request_jwt_application_token(
        #                                     self._INTEGRATION_KEY,
        #                                     self._DS_AUTH_HOST,
        #                                     pk_bytes,
        #                                     TOKEN_EXPIRATION_IN_SECONDS
        #                                    )
        # print(jwt_token)
        if jwt_token is not None:
            self._access_token = jwt_token.access_token
            self._client.set_default_header("Authorization", jwt_token.token_type+ " " + self._access_token)

    # create envelope using a stored template in docusign
    def _make_tmpl_envelope(self,
                            template_id,
                            signer_name,
                            signer_email,
                            cc_name,
                            cc_email,
                            template_params):

        try:
            recipients = []

            recipient_tabs = {}
            tmpl_tabs = self.fetch_tabs(template_id)
            # add tabs only if template params is given
            if template_params is not None:
                recipient_tabs['textTabs'] = [] 

                for key, value in template_params.items():
                    if key in tmpl_tabs['text_tabs'].keys():
                        #print(key)
                        tab = tmpl_tabs['text_tabs'][key] 
                        tab.value = value
                        recipient_tabs['textTabs'].append(tab)

            recipient_tabs['signHereTabs'] = []
            for tab in tmpl_tabs['signhere_tabs']:
                recipient_tabs['signHereTabs'].append(tab) 

            recipient_tabs['initialHereTabs'] = []
            for tab in tmpl_tabs['initial_here_tabs']:
                recipient_tabs['initialHereTabs'].append(tab)

            # Signer 
            signer = TemplateRole(email=signer_email,
                                  name=signer_name,
                                  role_name='signer',
                                  tabs=recipient_tabs)
            #print(signer)
            recipients.append(signer)

            if cc_email is not None:
                # Recepient
                cc = TemplateRole(email=cc_email,
                                  name=cc_name,
                                  role_name = 'cc')
                recipients.append(cc)

            # create an envelope definition
            envelope_definition = EnvelopeDefinition(status='sent',
                                                     template_id=template_id) 
            envelope_definition.template_roles = recipients

        except Exception as err:
            raise ValueError('Error in creating envelope >> {}'.format(str(err))) 

        return envelope_definition

    def _make_doc_envelope(self,
                           doc_path,
                           doc_name,
                           signer_name,
                           signer_email,
                           cc_name,
                           cc_email):

        try:
            recipients = []

            with open(os.path.join(doc_path, doc_name), "rb") as file:
                content_bytes = file.read()
            base64_file_content = base64.b64encode(content_bytes).decode('ascii') 

            document = Document( # create the DocuSign document object 
                document_base64 = base64_file_content, 
                name = doc_name, # can be different from actual file name
                file_extension = 'pdf', # many different document types are accepted
                document_id = 1 # a label used to reference the doc
            )

            signer = Signer( # The signer
                            email = signer_email, 
                            name = signer_name,
                            recipient_id = "1",  
                            routing_order = "1")
            recipients.append(signer)

            if cc_email is not None:
                # Recepient
                cc = TemplateRole(email=cc_email,
                                  name=cc_name,
                                  role_name = 'cc')
                recipients.append(cc)

            envelope_definition = EnvelopeDefinition(
                email_subject = self._EMAIL_SUBJECT,
                documents = [document], # The order in the docs array determines the order in the envelope
                recipients = Recipients(signers = recipients), # The Recipients object wants arrays for each recipient type
                status = "sent" # requests that the envelope be created and sent.
            )

            # create an envelope definition
            envelope_definition = EnvelopeDefinition(status='sent',
                                                     template_id=template_id)
            envelope_definition.template_roles = recipients

        except Exception as err:
            raise ValueError('Error in creating envelope >> {}'.format(str(err)))

        return envelope_definition

    # interface for requesting signature for a document
    def send_document_for_signing(self,
                                  doc_path,
                                  doc_name, # document with absolute path
                                  signer_name,
                                  signer_email,
                                  cc_name=None,
                                  cc_mail=None):
        try: 
            if self._client is None:
                return None

            #make an envelope
            envelope = self._make_doc_envelope(doc_path, 
                                               doc_name, 
                                               signer_name, 
                                               signer_email, 
                                               cc_name, 
                                               cc_mail)

            envelope_api = EnvelopesApi(self._client);
            result = envelope_api.create_envelope(self._ACCOUNT_ID, 
                                                  envelope_definition=envelope);
            
            return result.envelope_id;

        except Exception as err: 
            print("Error in send document {}".format(str(err)))
            return None


    # API is used request signature for remote signing 
    def request_signature(self,
                          template_id, 
                          signer_name, 
                          signer_email, 
                          cc_name=None,
                          cc_mail=None,
                          template_params=None): 

        try: 
            if self._client is None:
                return None

            #make an envelope
            envelope = self._make_tmpl_envelope(template_id, 
                                                signer_name, signer_email, 
                                                cc_name, cc_mail,
                                                template_params)
            envelope_api = EnvelopesApi(self._client)
            
            result = envelope_api.create_envelope(self._ACCOUNT_ID, envelope_definition=envelope);
            print(result)
            return result.envelope_id;

        except Exception as err: 
            print("Error in requesting signature {}".format(str(err)))
            return None

    def envelope_status(self, 
                        envelope_id):
        try:
            envelope_api = EnvelopesApi(self._client)
            result = envelope_api.get_envelope(self._ACCOUNT_ID, envelope_id=envelope_id)
            print(result)
            return result.status

        except Exception as err:
            print("Error in envelope status {}".format(str(err)))

    def envelopes_status(self, from_date):
        try:
            status_list = []
            envelope_api = EnvelopesApi(self._client)
            result = envelope_api.list_status_changes(self._ACCOUNT_ID, from_date = from_date) 
            for envelope in result.envelopes:
                status = {}
                status['id'] = envelope.envelope_id
                status['status'] = envelope.status
                status_list.append(status)

            print(status_list)

        except Exception as err: 
            print("Error in envelopes status {}".format(str(err)))

    """
    Fetch template details from the docuserver
    """
    def fetch_templates(self):
        try:
            template_list = []
            template_api = TemplatesApi(self._client)
            result = template_api.list_templates(self._ACCOUNT_ID)
            for tmpl in result.envelope_templates:
                template = {}
                template['name'] = tmpl.name
                template['id']   = tmpl.template_id
                template_list.append(template)

            print(template_list)
            return template_list
        except Exception as err:
            print("Error in fetch templates {}".format(str(err)))

    def fetch_template_documents(self, template_id):
        try:
            document_list = []
            template_api = TemplatesApi(self._client)
            result = template_api.list_documents(DS_ACCOUNT_ID, template_id)
            for doc in result.template_documents:
                print(doc.document_id)
                print(doc.name)

        except Exception as err:
            print("Error in fetch documents {}".format(str(err)))

    def fetch_tabs(self, template_id):
        try:
            tabs = {}
            tabs['text_tabs'] = {}
            tabs['signhere_tabs'] = []
            tabs['initial_here_tabs'] = []

            template_api = TemplatesApi(self._client)
            result = template_api.get(DS_ACCOUNT_ID, template_id)
            num_pages = int(result.page_count)
            page = 0
            while page < num_pages:
                page = page + 1
                result = template_api.get_page_tabs(DS_ACCOUNT_ID, 1, page, template_id)
                if result.text_tabs is not None:
                    for tab in result.text_tabs:
                        tabs['text_tabs'][tab.tab_label] = tab

                if result.sign_here_tabs is not None:
                    for tab in result.sign_here_tabs:
                        tabs['signhere_tabs'].append(tab)

                if result.initial_here_tabs is not None:
                    for tab in result.initial_here_tabs:
                        tabs['initial_here_tabs'].append(tab)

            return tabs 
                
        except Exception as err:
            print("Error in fetch documents {}".format(str(err)))

elite_dms_contract1_signed = '5ac45a69-e135-4ff3-8547-67abf0d50b3a'
elite_dms_contract2_signed = 'ffb8ec43-3574-4343-a140-ccd7c6807d2f'

# test - request signature for template
def send_for_signature(name, email):
    ds = DocuSign()
    ds.authorize()
    key = ds.request_signature(template_id=elite_dms_contract2_signed, 
                               signer_name=name, 
                               signer_email=email, 
                               template_params=_test_contract_params)
    if key is not None:
        print("Envelope send {}".format(key))
   
# test - envelope status
def fetch_envelope_status():
    ds = DocuSign() 
    ds.authorize()
    ds.envelope_status('7abba087-3ba4-4ee2-b61f-00628c6073bb')
    

def fetch_envelopes_status(hrs=24):    
    ds = DocuSign()
    ds.authorize()
    from_date = (datetime.now() - timedelta(hours=hrs)).isoformat()
    ds.envelopes_status(from_date)

