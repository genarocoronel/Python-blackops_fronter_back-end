from zeep import Client
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep.transports import Transport

from lxml import etree
import requests

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
            self._client = Client(wsdl=self._WSDL_URL, transport=Transport(session=session))
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
            headers = {'content-type': 'text/xml'}
            body = "<?xml version='1.0' encoding='UTF-8'?>{}".format(xml)
            response = requests.post(self._WSDL_URL, data=body, headers=headers)
            print(response.text)
        except Exception as err:
            logging.warning('EPPS client raw request issue ')


    def add_card(self, card_holder):
        try:
        kwargs = card_holder.to_dict() 
        kwargs['UserName'] = self._EPPS_UNAME
        kwargs['PassWord'] = self._EPPS_PSWD
        response = self._client.service.AddCardHolder(**kwargs) 
        print(response)
        except Exception as err:
            logging.warning()
        
# test methods
    
from datetime import datetime

def test_card_holder():
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

def test_add_card():
    e = EppsClient()
    e.connect()
    
    ch = test_card_holder()
    e.add_card(ch)


def test_raw():
    e = EppsClient()
    e.connect()
    ch = test_card_holder()
    e._raw_request("AddCardHolder", ch.to_dict())
