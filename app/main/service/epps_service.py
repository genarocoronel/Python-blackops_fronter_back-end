from zeep import Client as SoapClient
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep.transports import Transport

from lxml import etree
import requests
import enum
import logging

class CardHolder(object):

    def __init__(self):
        self._id = None  # mandatory
        self._first_name = None # mandatory 
        self._last_name = None # mandatory
        self._dob = None
        self._ssn = None
        self._street = None # mandatory
        self._city = None # mandatory
        self._state  = None # mandatory
        self._zip = None # mandatory
        self._phone_no = None
        self._email = None

    @property
    def id(self): return self._id
    @id.setter
    def id(self, id):
        self._id = id
    @property
    def first_name(self): return self._first_name
    @first_name.setter
    def first_name(self, fname):
        self._first_name = fname
    @property
    def last_name(self): return self._last_name
    @last_name.setter
    def last_name(self, lname):
        self._last_name = lname
    @property
    def dob(self): return self._dob
    @dob.setter
    def dob(self, dob):
        self._dob = dob
    @property
    def ssn(self): return self._ssn
    @ssn.setter
    def ssn(self, ssn):
        self._ssn = ssn
    @property
    def street(self): return self._street
    @street.setter
    def street(self, street):
        self._street = street
    @property
    def city(self): return self._city
    @street.setter
    def city(self, city):
        self._city = city
    @property
    def state(self): return self._state
    @state.setter
    def state(self, state):
        self._state = state
    @property
    def zip(self): return self._zip
    @zip.setter
    def zip(self, zip):
        self._zip = zip
    @property
    def phone(self): return self._phone_no
    @phone.setter
    def phone(self, phone):
        self._phone_no = phone
    @property
    def email(self): return self._email
    @email.setter
    def email(self, email):
        self._email = email
 
    def to_dict(self):
        result = {'CardHolderID':self._id, 'FirstName': self._first_name, 'LastName': self._last_name,
                  'Street': self._street, 'City': self._city, 'State': self._state,
                  'Zip': self._zip, 'DateOfBirth': self._dob }
        if self._ssn is not None:
            result['SSN'] = self._ssn
        if self._phone_no is not None:
            result['PhoneNumber'] = self._phone_no 
        if self._email is not None:
            result['EmailAddress'] = self._email
                  
        return result

    def is_valid(self):
        # id
        if self._id is None:
            return False
        # name
        elif self._first_name is None or self._last_name is None or self._dob is None:
            return False
        elif self._street is None or self._state is None or self._zip is None:
            return False

        return True

class EftStatus(enum.Enum):
    Pending = "Create EFT Pending"
    Transmitted = "Transmitted"
    Settled = "Settled"
    Returned = "Returned"
    Voided = "Voided"
    Failed = "Failed"
    Error = "Error"

class Eft(object):
    
    def __init__(self):
        self._id = None
        self._date = None
        self._amount = None
        self._fee = None
        self._bank_name = None
        self._bank_city = None
        self._bank_state = None 
        self._account_no = None
        self._routing_no = None
        self._account_type = None
        self._memo = None 
        self._transaction_id = None
        self._status = None
        self._message = None
   
    @property
    def id(self): return self._id
    @id.setter
    def id(self, id):
        self._id = id  
    @property
    def date(self): return self._date
    @date.setter
    def date(self, date):
        self._date = date
    @property
    def amount(self): return self._amount
    @amount.setter
    def amount(self, amount):
        self._amount = amount
    @property
    def fee(self): return self._fee
    @fee.setter
    def fee(self, fee):
        self._fee = fee
    @property
    def bank_name(self): return self._bank_name
    @bank_name.setter
    def bank_name(self, bank_name):
        self._bank_name = bank_name
    @property
    def bank_city(self): return self._bank_city
    @bank_city.setter
    def bank_city(self, bank_city):
        self._bank_city = bank_city
    @property
    def bank_state(self): return self._bank_state
    @bank_state.setter
    def bank_state(self, bank_state):
        self._bank_state = bank_state
    @property
    def account_no(self): return self._account_no
    @account_no.setter
    def account_no(self, account_no):
        self._account_no = account_no
    @property
    def routing_no(self): return self._routing_no
    @routing_no.setter
    def routing_no(self, routing_no):
        self._routing_no = routing_no
    @property
    def account_type(self): return self._account_type
    @account_type.setter
    def account_type(self, account_type):
        self._account_type = account_type
    @property
    def memo(self): return self._memo
    @memo.setter
    def memo(self, memo):
        self._memo = memo
    # Non setter properties
    @property
    def transaction_id(self): return self._transaction_id
    @transaction_id.setter
    def transaction_id(self, trans_id):
        self._transaction_id = trans_id
    @property
    def status(self): return self._status
    @status.setter
    def status(self, status):
        self._status = status
    @property
    def message(self): return self._message
    @message.setter
    def message(self, msg):
        self._message = msg
 
    def to_dict(self):
        result = {'CardHolderID': self._id, 'EftDate': self._date, 'EftAmount': self._amount, 
                  'AccountNumber': self._account_no, 'RoutingNumber': self._routing_no, 
                  'AccountType': self._account_type}

        if self._fee is not None:
            result['EftFee'] = self._fee
        if self._bank_name is not None:
            result['BankName'] = self._bank_name
        if self._bank_city is not None:
            result['BankCity'] = self._bank_city
        if self._bank_state is not None:
            result['BankState'] = self._bank_state
        if self._memo is not None:
            result['Memo'] = self._memo
        return result

    def from_response(self, message):
        if 'EFTList' not in message:
            self._status = EftStatus.Failed 
        else:
            data = message['EFTList']['EFTTransactionDetail'][0]
            self._id = data['CardHolderId']
            self._amount = data['EftAmount']
            self._transaction_id = data['EftTransactionID']
            self._status = EftStatus(data['StatusCode'])
            self._message = data['LastMessage']
            self._date = data['EftDate']



class FeeType(enum.Enum):
    VendorFee = 'VendorFee'
    SettlementPayment = 'SettlementPayment'

# EFT Fee
class EftFee(object):
    
    def __init__(self):
        self._id = None  # mandatory
        self._date = None # mandatory
        self._amount = None # mandatory
        self._description = None
        self._fee_type = None # mandatory
        self._paid2name = None
        self._paid2phone = None
        self._paid2street = None
        self._paid2street2 = None
        self._paid2city = None
        self._paid2state = None
        self._paid2zip = None
        self._contact_name = None
        self._paid2customerno = None

    @property
    def id(self): return self._id
    @id.setter
    def id(self, id):
        self._id = id  
    @property
    def date(self): return self._date
    @date.setter
    def date(self, date):
        self._date = date
    @property
    def amount(self): return self._amount
    @amount.setter
    def amount(self, amount):
        self._amount = amount
    @property
    def description(self): return self._description
    @description.setter
    def description(self, description):
        self._description = description
    @property
    def fee_type(self): return self._fee_type
    @fee_type.setter
    def fee_type(self, fee_type):
        self._fee_type = fee_type

    def set_settlement_party(self, name, phone, street, street2, city, state, zip, contact_name, customer_no): 
        self._paid2name = name
        self._paid2phone = phone
        self._paid2street = street
        self._paid2street2 = street2
        self._paid2city = city
        self._paid2state = state
        self._paid2zip = zip
        self._contact_name = contact_name
        self._paid2customerno = customer_no
 
    def to_dict(self):
        result = {'CardHolderID': self._id, 'FeeDate':self._date, 'FeeAmount': self._amount,
                  'FeeType':self._fee_type}       
        # optional
        if self._description is not None:
            result['Description'] = self._description 

        if self._fee_type == FeeType.SettlementPayment:
            result['PaidToName'] = self._paid2name 
            result['PaidToStreet'] = self._paid2street
            result['PaidToCity'] = self._paid2city
            result['PaidToState'] = self._paid2state
            result['PaidToZip'] = self._paid2zip
            # optional fields
            if self._paid2phone is not None:
                result['Paid2Phone'] = self._paid2phone
            if self._paid2street2 is not None:
                result['PaidToStreet2'] = self._paid2street2
            if self._contact_name is not None:
                result['ContactName'] = self._contact_name
            if self._paid2customerno is not None:
                result['PaidToCustomerNumber'] = self._paid2customerno

        return result

class EppsClient(object):
    _WSDL_URL = "https://www.securpaycardportal.com/proxy/proxy.incoming/eftservice.asmx?wsdl"
    _EPPS_UNAME = "TESTDSS_API"
    _EPPS_PSWD = "TestDSS1216"

    def __init__(self):
        # initialize globals 
        pass

    def connect(self):
        try:
            session = Session()
            session.auth = HTTPBasicAuth(self._EPPS_UNAME, self._EPPS_PSWD)
            self._client = SoapClient(wsdl=self._WSDL_URL, transport=Transport(session=session))
            # change the binding address
            self._client.service._binding_options['address'] = self._WSDL_URL
        except Exception as err:
            logging.warning('EPPS client connect issue')            

    def _raw_request(self, service_name, kwargs):
        try:
            kwargs['UserName'] = self._EPPS_UNAME
            kwargs['PassWord'] = self._EPPS_PSWD
            # create raw message        
            message = self._client.create_message(self._client.service, service_name, **kwargs)
            xml = etree.tostring(message)
            xml = xml.decode("utf-8")
            print(xml)
            headers = {'content-type': 'text/xml'}
            body = "<?xml version='1.0' encoding='UTF-8'?>{}".format(xml)
            response = requests.post(self._WSDL_URL, data=body, headers=headers)
            print(response.text)
        except Exception as err:
            logging.warning('EPPS client raw request issue ')

    def add_card_holder(self, card_holder):
        try:
            kwargs = card_holder.to_dict() 
            kwargs['UserName'] = self._EPPS_UNAME
            kwargs['PassWord'] = self._EPPS_PSWD
            response = self._client.service.AddCardHolder(**kwargs) 
            print(response)
        except Exception as err:
            logging.warning("EppsClient add card issue")
    """
    Update card holder 
    """
    def update_card_holder(self, card_holder):
        try:
            kwargs = {'CardHolderID': card_holder.id, 'Street':card_holder.street, 'City': card_holder.city,
                      'State': card_holder.state, 'Zip': card_holder.zip } 
            if card_holder.phone is not None:
                kwargs['PhoneNumber'] = card_holder.phone
            if card_holder.email is not None:
                kwargs['EmailAddress'] = card_holder.email

            kwargs['UserName'] = self._EPPS_UNAME
            kwargs['PassWord'] = self._EPPS_PSWD
            response = self._client.service.UpdateCardHolder(**kwargs) 
            
        except Exception as err:
            logging.warning("EppsClient update card issue")

    """
    Response Statuses:
     - Create EFT Pending
     - Transmitted
     - Settled
     - Returned
     - Voided 
    """
    def register_eft(self, eft):
        try:
            kwargs = eft.to_dict() 
            kwargs['UserName'] = self._EPPS_UNAME
            kwargs['PassWord'] = self._EPPS_PSWD
            print(kwargs)
            response = self._client.service.AddEft(**kwargs)
            print(response)
            if response['StatusCode'] is None:
                eft.status = EftStatus.Failed
                eft.message = response['Message']
            else:
                eft.status = EftStatus(response['StatusCode'])
                eft.transaction_id = response['EftTransactionID']
                eft.message = response['Message']

            return eft

        except Exception as err:
            print(str(err))
            logging.warning("EppsClient register EFT issue")

    """
    Find EFT by transaction
    """
    def find_eft_by_transaction(self, trans_id):
        try:
            kwargs = {}
            kwargs['UserName'] = self._EPPS_UNAME
            kwargs['PassWord'] = self._EPPS_PSWD
            kwargs['EFTTRansactionID'] = trans_id
            eft = Eft()
            response = self._client.service.FindEftByEFTTransactionID(**kwargs)
            if response['Message'] == 'Success':
                eft.from_response(response)
            else:
                eft.status = EftStatus.Failed
                 
            return eft

        except Exception as err:
            logging.warning("EppsClient find EFT by transaction {}".format(str(err)))

    """
    Find EFT by card holder id
    """
    def find_eft_by_holder(self, holder_id):
        try:
            kwargs = {}
            kwargs['UserName'] = self._EPPS_UNAME 
            kwargs['PassWord'] = self._EPPS_PSWD
            kwargs['CardHolderID'] = holder_id
            eft = Eft()
            response = self._client.service.FindEftByID(**kwargs)
            if response['Message'] == 'Success':
                eft.from_response(response)
            else:
                eft.status = EftStatus.Failed
                 
            return eft

        except Exception as err:
            logging.warning("EppsClient find EFT by holder {}".format(str(err)))


    # Add EFT fee
    def add_fee(self, fee):
        try:
            kwargs = fee.to_dict()
            kwargs['UserName'] = self._EPPS_UNAME
            kwargs['PassWord'] = self._EPPS_PSWD
            print(kwargs)
            response = self._client.service.AddFee(**kwargs)
            print(response)

        except Exception as err:
            logging.warning("EppsClient Add Fee issue") 
        
# test methods
    
from datetime import datetime

def card_holder():
    c = CardHolder()
    c.id = "123456789"
    c.first_name = "John"
    c.last_name = "Smith"
    c.ssn = "555111666"
    c.street = "Parkers West"
    c.city = "San Jose"
    c.state = "California"
    c.zip = "94088"
    c.phone = "7048012345"
    c.email = "test.dev15324@gmail.com"
    dt = datetime(1986, 12, 20, 0, 0)
    c.dob = dt

    return c

def eft():
    obj = Eft()
    obj.id = "123456789"
    obj.date = datetime(2019, 12, 26, 0, 0) 
    obj.amount = 1299.00
    obj.fee = 1200.00
    obj.bank_name = 'Bank of America'
    obj.bank_city = 'Sunnyvale'
    obj.bank_state = 'CA'
    obj.account_no = 2224446666
    obj.routing_no = 233344555
    obj.account_type = 'Checking'
    obj.memo = "Test memo"
    return obj

def eft_fee():
    obj = EftFee()
    obj.id = "123456789"
    obj.date = datetime(2019, 12, 26, 0, 0)
    obj.amount = 1299.00
    obj.description = "Add EFT Fee"
    obj.fee_type = "SettlementPayment"
    obj.set_settlement_party(name='David', phone='234567900', street='Steet 1', 
                             street1='Street2', city='San Fransico', state='CA', zip=94311, 
                             contact_name='Jimber', customer_no=23456)
    return obj 

def test_add_card():
    e = EppsClient()
    e.connect()
    
    ch = card_holder()
    e.add_card_holder(ch)

def test_add_eft(epps):
    f = eft()
    return epps.register_eft(f)

def test_add_fee():
    f = eft_fee()
    e = EppsClient()
    e.connect()
    e.add_fee(f)

def test_raw():
    e = EppsClient()
    e.connect()
    ch = card_holder()
    e._raw_request("AddCardHolder", ch.to_dict())
