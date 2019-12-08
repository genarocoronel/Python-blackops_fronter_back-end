import os

from flask_restplus import Namespace, fields

from app.main.model import Language, Frequency
from app.main.model.candidate import CandidateImportStatus, CandidateStatus
from app.main.model.employment import FrequencyStatus
from app.main.model.client import ClientType
from app.main.model.address import AddressType
from app.main.model.credit_report_account import CreditReportSignupStatus
from app.main.service.auth_helper import Auth
from app.main.util import parsers


class FileToFilenameField(fields.String):
    def format(self, value):
        return os.path.basename(value) if value else ''


class AddressTypeField(fields.String):
    def format(self, value):
        if isinstance(value, AddressType):
            return value.name
        else:
            return 'unknown'


class AddressDto(object):
    api = Namespace('addresses', description='address related operations')
    address = api.model('address', {
        'public_id': fields.String(required=True),
        'candidate_id': fields.String(required=True),
        'client_id': fields.String(required=True),
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'fromDate': fields.Date(required=True),
        'toDate': fields.Date(required=True),
        'type': AddressTypeField(required=True)
    })
    new_address = api.model('new_address', {
        'candidate_id': fields.String(required=True),
        'client_id': fields.String(required=True),
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'fromDate': fields.Date(required=True),
        'toDate': fields.Date(required=True),
        'type': AddressTypeField(required=True)
    })


class FrequencyTypeField(fields.String):
    def format(self, value):
        if isinstance(value, Frequency):
            return value.name
        else:
            return 'UNKNOWN'


class CampaignDto(object):
    api = Namespace('campaigns', description='campaign related operations')
    campaign = api.model('campaign', {
        'public_id': fields.String(required=True),
        'name': fields.String(required=True),
        'description': fields.String(required=False),
        'phone': fields.String(required=False),
        'job_number': fields.String(required=True),
        'offer_expire_date': fields.String(required=True),
        'mailing_date': fields.String(required=True),
        'mailer_file': FileToFilenameField(required=False),
        'inserted_on': fields.DateTime()
    })
    new_campaign = api.model('new_campaign', {
        'name': fields.String(required=True),
        'description': fields.String(required=False),
        'phone': fields.String(required=True),
        'job_number': fields.String(required=True),
        'offer_expire_date': fields.String(required=True),
        'mailing_date': fields.String(required=True)
    })
    update_campaign = api.model('update_campaign', {
        'name': fields.String(required=False),
        'description': fields.String(required=False),
        'phone': fields.String(required=False),
        'job_number': fields.String(required=False),
        'offer_expire_date': fields.String(required=False),
        'mailing_date': fields.String(required=False)
    })


class UserDto:
    api = Namespace('users', description='user related operations')
    new_user = api.model('new_user', {
        'email': fields.String(required=True, description='user email address'),
        'username': fields.String(required=True, description='user username'),
        'password': fields.String(required=True, description='user password', example=Auth.generate_password()),
        'first_name': fields.String(required=True, description='user first name'),
        'last_name': fields.String(required=True, description='user last name'),
        'title': fields.String(required=True, description='user title', example='Administrator'),
        'language': fields.String(required=True, description='user language preference', example='en'),
        'personal_phone': fields.String(required=True, description='user personal phone number'),
        'voip_route_number': fields.String(required=False, description='user VOIP routing number')

    })
    update_user = api.model('update_user', {
        'email': fields.String(required=False, description='user email address'),
        'first_name': fields.String(required=False, description='user first name'),
        'last_name': fields.String(required=False, description='user last name'),
        'title': fields.String(required=False, description='user title', example='Administrator'),
        'language': fields.String(required=False, description='user language preference', example='en'),
        'personal_phone': fields.String(required=False, description='user personal phone number'),
        'voip_route_number': fields.String(required=False, description='user VOIP routing number')

    })
    user = api.model('user', {
        'email': fields.String(required=True, description='user email address'),
        'username': fields.String(required=True, description='user username'),
        'password': fields.String(required=True, description='user password'),
        'public_id': fields.String(description='user identifier'),
        'first_name': fields.String(required=True, description='user first name'),
        'last_name': fields.String(required=True, description='user last name'),
        'title': fields.String(required=True, description='user title'),
        'language': fields.String(required=True, description='user language preference'),
        'personal_phone': fields.String(required=True, description='user personal phone number'),
        'voip_route_number': fields.String(required=False, description='user VOIP routing number')
    })


class AuthDto:
    api = Namespace('auth', description='authentication related operations')
    user_auth = api.model('auth_details', {
        'username': fields.String(required=True, description='The user username'),
        'password': fields.String(required=True, description='The user password '),
    })
    password_reset_request = api.model('password_reset_request', {
        'query': fields.String(required=True, description='The user email, phone, or username')
    })
    validate_password_reset_request = api.model('validate_password_reset_request', {
        'code': fields.String(required=True, description='code sent to phone for password reset request')
    })
    password_reset = api.model('password_reset', {
        'password': fields.String(required=True, description='new password for password reset request')
    })


class AppointmentDto:
    api = Namespace('appointments', description='appointment related operations')
    appointment = api.model('appointment', {
        'client_id': fields.Integer(required=True, description='identifier for client'),
        'employee_id': fields.Integer(required=True, description='identifier for employee'),
        'datetime': fields.DateTime(required=True, description='date and time of appointment'),
        'summary': fields.String(required=True, description='summary of appointment'),
        'notes': fields.String(required=False, description='notes for appointment'),
        'reminder_types': fields.String(required=True, description='type(s) of reminders to be sent to client'),
        'status': fields.String(required=False, description='status of appointment'),
        'public_id': fields.String(description='user identifier')
    })


class LanguageField(fields.String):
    def format(self, value):
        if isinstance(value, Language):
            return value.name
        else:
            return 'UNKNOWN'


class ClientTypeField(fields.String):
    def format(self, value):
        if isinstance(value, ClientType):
            return value.name
        else:
            return 'unknown'


class FrequencyStatusField(fields.String):
    def format(self, value):
        if isinstance(value, FrequencyStatus):
            return value.name
        else:
            return 'unknown'


_credit_report_debt_model = {
    'debt_name': fields.String(),
    'creditor': fields.String(),
    'ecoa': fields.String(),
    'account_number': fields.String(),
    'account_type': fields.String(),
    'push': fields.Boolean(),
    'last_collector': fields.String(),
    'collector_account': fields.String(),
    'last_debt_status': fields.String(),
    'bureaus': fields.DateTime(),
    'days_delinquent': fields.Integer(),
    'balance_original': fields.Integer(),
    'payment_amount': fields.Integer(),
    'credit_limit': fields.Integer(),
    'graduation': fields.DateTime(),
    'last_update': fields.DateTime(required=True)
}


class ClientDto:
    api = Namespace('clients', description='client related operations')
    client = api.model('client', {
        'first_name': fields.String(required=True, description='client first name'),
        'last_name': fields.String(required=True, description='client last name'),
        'email': fields.String(required=True, description='client email address'),
        'language': LanguageField(required=True),
        'phone': fields.String(required=True, description='client phone number'),
        'type': ClientTypeField(required=False, description='client type'),
        'public_id': fields.String(description='client identifier'),
    })
    new_bank_account = api.model('new_bank_account', {
        'account_number': fields.String(required=True, description='client bank account number'),
        'routing_number': fields.String(required=True, description='client bank routing number')
    })
    bank_account = api.model('bank_account', {
        'bank_name': fields.String(required=True, description='client bank name'),
        'account_number': fields.String(required=True, description='client bank account number'),
        'routing_number': fields.String(required=True, description='client bank routing number'),
        'valid': fields.Boolean(required=True)
    })
    client_income = api.model('client_income', {
        'income_type_id': fields.Integer(required=True),
        'income_type': fields.String(required=True),
        'value': fields.Integer(required=True),
        'frequency': FrequencyTypeField(required=True),
    })
    update_client_income = api.model('update_client_income', {
        'income_type_id': fields.Integer(required=True),
        'value': fields.Integer(required=True),
        'frequency': FrequencyTypeField(required=True),
    })
    client_employment = api.model('client_employment', {
        'start_date': fields.DateTime(required=True),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=True),
        'gross_salary_frequency': FrequencyStatusField(),
        'other_income': fields.Float(required=True),
        'other_income_frequency': FrequencyStatusField(),
        'current': fields.Boolean(required=True, default=False)
    })
    update_client_employment = api.model('update_client_employment', {
        'start_date': fields.DateTime(required=True),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=True),
        'gross_salary_frequency': FrequencyStatusField(),
        'other_income': fields.Float(required=True),
        'other_income_frequency': FrequencyStatusField(),
        'current': fields.Boolean(required=True, default=False)
    })
    credit_report_debt = api.model('credit_report_debt', _credit_report_debt_model)
    client_monthly_expense = api.model('client_monthly_expense', {
        'expense_type_id': fields.Integer(required=True),
        'expense_type': fields.String(required=True),
        'value': fields.Integer(required=True),
    })
    update_client_monthly_expense = api.model('update_client_monthly_expense', {
        'expense_type_id': fields.Integer(required=True),
        'value': fields.Integer(required=True),
    })


class LeadDto:
    api = Namespace('leads', description='lead related operations')
    lead = api.model('lead', {
        'first_name': fields.String(required=True, description='lead first name'),
        'last_name': fields.String(required=True, description='lead last name'),
        'address': fields.String(required=True, description='client address'),
        'city': fields.String(required=True, description='client city'),
        'state': fields.String(required=True, description='client state'),
        'zip': fields.String(required=True, description='client zip'),
        'zip4': fields.String(required=True, description='client zip4'),
        'estimated_debt': fields.Integer(required=True, description='client estimated_debt'),
        'county': fields.String(required=True, description='client county'),
        'email': fields.String(required=True, description='lead email address'),
        'language': LanguageField(required=True),
        'phone': fields.String(required=True, description='lead phone number'),
        'type': ClientTypeField(required=False, description='client type'),
        'public_id': fields.String(description='lead identifier'),
    })
    credit_report_debt = api.model('credit_report_debt', _credit_report_debt_model)


class CandidateImportStatusField(fields.String):
    def format(self, value):
        if isinstance(value, CandidateImportStatus):
            return value.name
        else:
            return 'unknown'


class CandidateStatusField(fields.String):
    def format(self, value):
        if isinstance(value, CandidateStatus):
            return value.name
        else:
            return 'unknown'


class CreditReportAccountStatusField(fields.String):
    def format(self, value):
        if isinstance(value, CreditReportSignupStatus):
            return value.name
        else:
            return 'unknown'


class CandidateDto:
    api = Namespace('candidates', description='candidate related operations')
    credit_report_account = api.model('credit_report_account', {
        'public_id': fields.String(),
        'status': CreditReportAccountStatusField()
    })
    candidate = api.model('candidate', {
        'public_id': fields.String(),
        'first_name': fields.String(),
        'last_name': fields.String(),
        'middle_initial': fields.String(),
        'suffix': fields.String(),
        'address': fields.String(),
        'city': fields.String(),
        'state': fields.String(),
        'zip': fields.String(),
        'estimated_debt': fields.Integer(),
        'inserted_on': fields.DateTime(),
        'county': fields.String(),
        'email': fields.String(),
        'language': LanguageField(),
        'phone': fields.String(),
        'status': CandidateStatusField(),
        'disposition': fields.String(),
        'credit_report_account': fields.Nested(credit_report_account)
    })
    update_candidate = api.model('update_candidate', {
        'first_name': fields.String(),
        'last_name': fields.String(),
        'middle_initial': fields.String(),
        'suffix': fields.String(),
        'address': fields.String(),
        'city': fields.String(),
        'state': fields.String(),
        'zip': fields.String(),
        'county': fields.String(),
        'email': fields.String(),
        'language': LanguageField(),
        'phone': fields.String(),
        'status': CandidateStatusField()

    })
    candidate_employment = api.model('candidate_employment', {
        'start_date': fields.DateTime(required=True),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=False),
        'gross_salary_frequency': FrequencyStatusField(),
        'other_income': fields.Float(required=False),
        'other_income_frequency': FrequencyStatusField(required=False),
        'current': fields.Boolean(required=True, default=False)
    })

    update_candidate_employment = api.model('update_candidate_employment', {
        'start_date': fields.DateTime(),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=False),
        'gross_salary_frequency': FrequencyStatusField(required=False),
        'other_income': fields.Float(required=False),
        'other_income_frequency': FrequencyStatusField(required=False),
        'current': fields.Boolean(required=True, default=False)
    })
    candidate_number = api.model('candidate_number', {
        'phone_type_id': fields.Integer(required=True),
        'phone_type': fields.String(required=True),
        'phone_number': fields.String(required=True),
        'preferred': fields.Boolean(required=True, default=False)
    })
    update_candidate_number = api.model('update_candidate_number', {
        'phone_type_id': fields.Integer(required=True),
        'phone_number': fields.String(required=True),
        'preferred': fields.Boolean(required=True, default=False)
    })
    candidate_income = api.model('candidate_income', {
        'income_type_id': fields.Integer(required=True),
        'income_type': fields.String(required=True),
        'value': fields.Integer(required=True),
        'frequency': FrequencyTypeField(required=True),
    })
    update_candidate_income = api.model('update_candidate_income', {
        'income_type_id': fields.Integer(required=True),
        'value': fields.Integer(required=True),
        'frequency': FrequencyTypeField(required=True),
    })
    candidate_monthly_expense = api.model('candidate_monthly_expense', {
        'expense_type_id': fields.Integer(required=True),
        'expense_type': fields.String(required=True),
        'value': fields.Integer(required=True),
    })
    update_candidate_monthly_expense = api.model('update_candidate_monthly_expense', {
        'expense_type_id': fields.Integer(required=True),
        'value': fields.Integer(required=True),
    })
    tasks = api.model('import_task', {
        'name': fields.String(),
        'description': fields.String(),
        'message': fields.String(),
        'complete': fields.Boolean(),
        'progress': fields.Integer()
    })
    imports = api.model('candidate_import_request', {
        'public_id': fields.String(required=True),
        'file': FileToFilenameField(required=True),
        'status': CandidateImportStatusField(required=True),
        'inserted_on': fields.DateTime(required=True),
        'updated_on': fields.DateTime(required=True),
        'tasks': fields.List(fields.Nested(tasks))
    })
    candidate_upload = parsers.file_upload
    new_credit_report_account = api.model('candidate_create_request', {
        'first_name': fields.String(required=True, example='Charlie'),
        'last_name': fields.String(required=True, example='Test-PJNDL'),
        'zip': fields.String(required=True, example='01001'),
        'phone': fields.String(required=True, example='555-555-5555')
    })
    update_credit_report_account = api.model('candidate_update_request', {
        'first_name': fields.String(required=True, example='Charlie'),
        'last_name': fields.String(required=True, example='Test-PJNDL'),
        'street': fields.String(required=True, example='111 Donkey Lane'),
        'street2': fields.String(required=False),
        'city': fields.String(required=False, example='Boston'),
        'state': fields.String(required=False, example='MA'),
        'zip': fields.String(required=True, example='01001'),
        'phone': fields.String(required=True, example='555-555-5555'),
        'dob': fields.String(required=True, example='01/01/1990'),
        'ssn': fields.String(required=False),
        'ssn4': fields.String(required=False),
        'security_question_id': fields.String(required=False),
        'security_question_answer': fields.String(required=False),
    })
    account_verification_answers = api.model('verification_question_answers', {
        'reference_number': fields.String(required=True),
        'answers': fields.Nested(api.model('answers_list', {
            'answer1': fields.String(required=True),
            'answer2': fields.String(required=True),
            'answer3': fields.String(required=True)
        }), required=True, skip_none=True)
    })


class TestAPIDto:
    api = Namespace('tests', description='Test operations for Dev/QA')
