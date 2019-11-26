from docusign_esign import ApiClient, EnvelopeDefinition, TemplateRole, EnvelopesApi, Configuration, Recipients, Document, Signer, Recipients, TemplatesApi
import base64, os
from datetime import datetime, timedelta
import time

DS_ACCOUNT_ID = '910decab-18f3-4eae-8456-74552da97b03'

TOKEN_REPLACEMENT_IN_SECONDS = 10 * 60
TOKEN_EXPIRATION_IN_SECONDS = 3600

TEST_ENVELOPE_TABS = {  
 "textTabs":[
  {
    "tabLabel": "ClientFirstName",
    "value": "Trevos",
    "documentId": "1",
    "pageNumber": "1",
    "xPosition":"115","yPosition":"175"
  },
  {
    "tabLabel": "ClientLastName",
    "value": "Smith",
    "documentId": "1",
    "pageNumber": "1",
    "xPosition":"343","yPosition":"175"
  },
  {
    "tabLabel": "ClientAddress",
    "value": "1234, queens blvd, San Jose",
    "documentId": "1",
    "pageNumber": "1",
    "xPosition":"115","yPosition":"200"
  },
  {
    "tabLabel": "ClientState",
    "value": "CA",
    "documentId": "1",
    "pageNumber": "1",
    "xPosition":"115","yPosition":"273"
  },
  {
    "tabLabel": "ClientZip",
    "value": "92111",
    "documentId": "1",
    "pageNumber": "1"
  },
  ],

  "signHereTabs": [{
                    "xPosition": "100",
                    "yPosition": "100",
                    "documentId": "1",
                    "pageNumber": "1"
                }],
                "initialHereTabs": [{
                    "xPosition": "200",
                    "yPosition": "100",
                    "documentId": "1",
                    "pageNumber": "1"
                }]
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
        print(jwt_token)
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
                            tabs):

        try:
            recipients = []
            # Signer 
            signer = TemplateRole(email=signer_email,
                                  name=signer_name,
                                  role_name='signer',
                                  tabs=tabs)
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
                          tabs=None): 

        try: 
            if self._client is None:
                return None

            #make an envelope
            envelope = self._make_tmpl_envelope(template_id, 
                                                signer_name, signer_email, 
                                                cc_name, cc_mail,
                                                tabs)
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

    def fetch_page_tabs(self, template_id, doc_id, page_num):
        template_api = TemplatesApi(self._client)
        result = template_api.get_page_tabs(DS_ACCOUNT_ID, doc_id, page_num, template_id) 
        print(result)

    def update_tabs(self, template_id, recipient_id):
        try:
            kwargs = {}
            kwargs['template_tabs'] = TEST_ENVELOPE_TABS
            template_api = TemplatesApi(self._client)
            result = template_api.update_tabs(DS_ACCOUNT_ID, recipient_id=1, template_id=template_id, **kwargs)
            print(result)
            

        except Exception as err:
            print("Error in update tabs {}".format(str(err)))



nda_template_id = '8d29c360-f878-48e2-9782-8914679ecdac'
tmpl1 = '9f12ec63-484c-4d84-ad73-5aa33455e827'
tmpl2 = 'ffb8ec43-3574-4343-a140-ccd7c6807d2f'

elite_dms_contract1_signed = '5ac45a69-e135-4ff3-8547-67abf0d50b3a'

# test - request signature for template
def send_for_signature(name, email):
    ds = DocuSign()
    ds.authorize()
    key = ds.request_signature(template_id=elite_dms_contract1_signed, 
                               signer_name=name, 
                               signer_email=email, 
                               tabs=TEST_ENVELOPE_TABS)
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

