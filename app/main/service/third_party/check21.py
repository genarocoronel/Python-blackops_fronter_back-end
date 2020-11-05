from zeep import Client as SoapClient
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep.transports import Transport
from lxml import etree

import xml.etree.ElementTree as ET
from flask import current_app as app
import requests
import logging
# zeep logging set to ERROR
logging.getLogger('zeep').setLevel(logging.ERROR)

class Check(object):
    _MEMO_TXT = 'Financial Program Payment'

    def __init__(self):
        self._payer = None
        self._addr1 = None
        self._addr2 = None
        self._addr3 = None
        self._check_date = None
        self._payee = None
        self._amount = None
        self._transit_no = None
        self._dda_no = None
        self._check_no = None
        self._memo = self._MEMO_TXT
        self._signature = None

    # payer
    @property
    def payer(self): return self._payer
    @payer.setter
    def payer(self, value):
        self._payer = value

    # payer addr1
    @property
    def addr1(self): return self._addr1
    @addr1.setter
    def addr1(self, value):
        self._addr1 = value
   
    # payer addr2
    @property
    def addr2(self): return self._addr2
    @addr2.setter
    def addr2(self, value):
        self._addr2 = value
   
    # payer addr3
    @property
    def addr3(self): return self._addr3
    @addr3.setter
    def addr3(self, value):
        self._addr3 = value

    # check date
    @property
    def check_date(self): return self._check_date
    @check_date.setter
    def check_date(self, value):
        self._check_date = value
   
    # payee
    @property
    def payee(self): return self._payee
    @payee.setter
    def payee(self, value):
        self._payee = value
   
    # amount
    @property
    def amount(self): return self._amount
    @amount.setter
    def amount(self, value):
        self._amount = value

    # routing/transit number
    @property
    def transit_no(self): return self._transit_no 
    @transit_no.setter
    def transit_no(self, value):
        self._transit_no = value

    # account number
    @property
    def dda_no(self): return self._dda_no
    @dda_no.setter
    def dda_no(self, value):
        self._dda_no = value

    # check number
    @property 
    def check_no(self): return self._check_no
    @check_no.setter
    def check_no(self, value):
        self._check_no = value

    #memo
    @property 
    def memo(self): return self._memo
    @memo.setter
    def memo(self, value):
        self._memo = value

    # signature
    @property 
    def signature(self): return self._signature
    @signature.setter
    def signature(self, value):
        self._signature = value

    # check_id
    @property
    def check_id(self): return self._check_id
    @check_id.setter
    def check_id(self, value):
        self._check_id = value
    # entry class
    @property
    def entry_class(self): return self._entry_class
    @entry_class.setter
    def entry_class(self, value):
        self._entry_class = value
    # post_date
    @property
    def post_date(self): return self._post_date
    @post_date.setter
    def post_date(self, value):
        self._post_date = value
    # send to fed flag
    @property
    def send_status(self): return self._send_status
    @send_status.setter
    def send_status(self, value):
        self._send_status = value
    # return status
    @property
    def ret_status(self): return self._ret_status
    @ret_status.setter
    def ret_status(self, value):
        self._ret_status = value

    def to_req_params(self):
        result = {}
        result['PayerName'] = self._payer
        result['PayerAddr1'] = self._addr1
        result['PayerAddr2'] = self._addr2
        result['PayerAddr3'] = self._addr3
        result['CheckDate'] = self._check_date.strftime("%m/%d/%Y")
        result['PayeeName'] = self._payee
        result['Amount'] = self._amount
        result['TransitNumber'] = self._transit_no
        result['DDANumber'] = self._dda_no
        result['CheckNumber'] = self._check_no
        result['MemoText'] = self._memo
        result['SignatureText'] = self._signature

        return result

    def parse(self, message):
        info = message
        #print(info)
        self.check_id = info['CheckID']
        self.check_no = info['CheckNumber']
        self.transit_no = info['TransitNumber']
        self.dda_no = info['DDANumber']
        self.amount = info['CheckAmount']
        self.entry_class = info['EntryClass']
        self.post_date = info['PostingDate']
        self.send_status = info['SentToFed']
        self.ret_status = info['ReturnStatus'] 
        self.payer = info['IndividualName']

class CreateCheckError(object):
    
    @staticmethod
    def to_string(code):
        result = 'NA'
         
        error = {
            10000: 'Not authorized (401)',
            10003: 'Base 64 string not valid (403)',
            10005: 'Parameter error (400)',
            10006: 'Client not authorized (401)',
            10011: 'Duplicate item (403)',
            10012: 'Transaction exceeds client transaction limit (403)',
            10013: 'Check amount causes daily total to exceed daily limit (403)',
            10014: 'Check amount causes monthly total to exceed monthly limit (403)',
            10015: 'RDFI not qualified to participate (403)',
            10016: 'Corporate customer advises not authorized (403)',
            10017: 'CheckNotPreviouslyAuthorized (403)',
            10019: 'Error in addenda sent (400)',
            10020: 'Addenda not supported for entry class (403)',
            10022: 'Auxiliar On-Us detected in MICR line for ACH item (ineligible) (403)',
        }
        if code in error:
            result = error[code] 

        return result

# SOAP Web Service
class Check21Client(object):
    WSDL_URL = 'https://gateway.acheck21.com/GlobalGateway/WebServices/Gateway/2.8/Service.asmx?WSDL'

    def __init__(self):
        self._user = app.config['CHECK21_USERNAME']
        self._pswd = app.config['CHECK21_PASSWORD']
        self._account_id = app.config['CHECK21_CLIENTID']

    def connect(self):
        try:
            session = Session()
            session.auth = HTTPBasicAuth(self._user, self._pswd)
            self._client = SoapClient(wsdl=self.WSDL_URL, transport=Transport(session=session))
            # change the binding address
            self._client.service._binding_options['address'] = self.WSDL_URL

        except Exception as err:
            app.logger.warning('Check21 SOAP client connect issue {}'.format(str(err)))

    # access testing
    def fetch_details(self):
        try:
            kwargs = {}
            kwargs['Username'] = self._user
            kwargs['Password'] = self._pswd
            kwargs['ClientID'] = self._account_id
            response = self._client.service.GetClient(**kwargs)
            print(response)

            # fetch the user
            kwargs = {}
            kwargs['Username'] = self._user
            kwargs['Password'] = self._pswd
            kwargs['SearchUser'] = self._user
            response = self._client.service.GetUser(**kwargs)
            print(response)

        except Exception as err:
            app.logger.warning('Check21 SOAP Fetch client {}'.format(str(err)))

    def fetch_eft(self, check):
        try:
            kwargs = {}
            kwargs['Username'] = self._user
            kwargs['Password'] = self._pswd
            kwargs['CheckID'] = check.check_id
            response = self._client.service.GetCheck(**kwargs)
            #print(response)
            code = response['Code']
            if code == 0:
                message = response['CheckInfo']
                check.parse(message)
                return {
                    'success': True,
                }
            else:
                message = response['Message']
                return {
                    'success': False,
                    'message': message
                } 

        except Exception as err:
            app.logger.warning('Check21Client Fetch EFT {}'.format(str(err)))
     
    def create_eft(self, check):
        try:
            kwargs = check.to_req_params()
            kwargs['Username'] = self._user
            kwargs['Password'] = self._pswd
            kwargs['ClientID'] = self._account_id

            response = self._client.service.CreateRCC(**kwargs)
            #print(response)
            code = response['Code']
            if code == 0:    
                check_id = response['CheckID']
                check.check_id = check_id
                return {
                    'success': True,
                }
            else:
                message = response['Message']
                return {
                    'success': False,
                    'message': message,
                }
           

        except Exception as err:
            app.logger.warning('Check21 Create RCC {}'.format(str(err)))

    def fetch_check_details(self, check): 
        try:
            kwargs = {}
            kwargs['Username'] = self._user
            kwargs['Password'] = self._pswd
            kwargs['ClientID'] = self._account_id
            kwargs['Query'] = '<CheckID><Operation>Equal</Operation><Value>{}</Value></CheckID>'.format(check.check_id)
            response = self._client.service.FindChecksDetails(**kwargs)
            code = response['Code']
            if code == 0:
                if 'Checks' in response:
                    checks = response['Checks'] 
                    cklist = checks['CheckInfo']
                    if len(cklist) > 0:
                        message = cklist[0]
                        check.parse(message)
                        return {
                            'success': True,
                        }
            else:
                message = response['Message']
                return {
                    'success': False,
                    'message': message,
                }
            
        except Exception as err:
            app.logger.warning('Check21 Fetch Returns {}'.format(str(err)))

    def fetch_returns_details(self, frm_date, to_date):
        try:
            check_list = []
            kwargs = {}
            kwargs['Username'] = self._user
            kwargs['Password'] = self._pswd
            kwargs['ClientID'] = self._account_id
            kwargs['Query'] = '<UploadDate><Operation>Between</Operation><Value>{}</Value><Value>{}</Value></UploadDate>'.format(frm_date, to_date)
            response = self._client.service.FindReturnsDetails(**kwargs)
            code = response['Code']
            if code == 0:
                if 'Checks' in response:
                    checks = response['Checks']
                    cklist = checks['CheckInfo']
                    if len(cklist) > 0:
                        for item in cklist:
                            ck = Check()
                            ck.parse(item)
                            check_list.append(ck)

                return {
                    'success': True,
                    'checks': check_list,
                }

            else:
                message = response['Message']
                return {
                    'success': False,
                    'message': message,
                }

        except Exception as err:
            app.logger.warning('Check21 Fetch Returns {}'.format(str(err)))

    def fetch_checks_details(self, frm_date, to_date):
        try:
            check_list = []
            kwargs = {}
            kwargs['Username'] = self._user
            kwargs['Password'] = self._pswd
            kwargs['ClientID'] = self._account_id
            kwargs['Query'] = '<UploadDate><Operation>Between</Operation><Value>{}</Value><Value>{}</Value></UploadDate>'.format(frm_date, to_date)
            response = self._client.service.FindChecksDetails(**kwargs)
            code = response['Code']
            if code == 0:
                if 'Checks' in response:
                    checks = response['Checks']
                    cklist = checks['CheckInfo']
                    if len(cklist) > 0:
                        for item in cklist:
                            print(item)
                            ck = Check()
                            ck.parse(item)
                            check_list.append(ck)

                return {
                    'success': True,
                    'checks': check_list,
                }

            else:
                message = response['Message']
                return {
                    'success': False,
                    'message': message,
                }

        except Exception as err:
            app.logger.warning('Check21 Fetch Returns {}'.format(str(err)))

# REST Service
class Check21(object):
    GATEWAY_URL = 'https://gateway.acheck21.com/GlobalGateway/REST'
    ENTRY_CLASS = 'WEB'
    
    def __init__(self):
        # initialize globals
        self._user = app.config['CHECK21_USERNAME']
        self._pswd = app.config['CHECK21_PASSWORD']
        self._client_id = app.config['CHECK21_CLIENTID']

    ## API testing 
    def fetch_client(self):
        try:
            client_id = ''
            path = '/client/{}'.format(self._client_id)
            url = "{}{}".format(self.GATEWAY_URL, path)
            print(url)
            response = requests.get(url, auth=(self._user, self._pswd))
            if response.ok:
                xml = ET.fromstring(response.content)
                client_id = xml.find('ClientID').text
                print(client_id)

            assert client_id == app.config['CHECK21_CLIENTID']

        except Exception as err:
            logging.warning('Check21 fetch client {}'.format(str(err)))
   
    
    # create check
    def create_check(self, check, client_tag):
        try:
            # build XML 
            url = 'https://gateway.acheck21.com/GlobalGateway/REST/check'

            params = {
                #'ClientID': self._client_id,
                'clientTag': client_tag,
                'individualName': check.owner,
                'checkNumber': check.number,
                'routingNumber': check.transit_no,
                'accountNumber': check.dda_no,
                'accountType': check.account_type,
                'amount': str(check.amount),
                'entryClass': self.ENTRY_CLASS
            }
            # API call
            response = requests.post(url, 
                                     json=params,
                                     auth=(self._user, self._pswd))

            return response

        except Exception as err:
            logging.warning('Check21 Create Check issue {}'.format(str(err)))

   
