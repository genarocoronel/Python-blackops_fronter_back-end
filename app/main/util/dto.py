import os

from flask_restplus import Namespace, fields

from app.main.model import Language, Frequency
from app.main.model.candidate import CandidateImportStatus, CandidateStatus, CandidateDispositionType
from app.main.model.employment import FrequencyStatus
from app.main.model.client import ClientType, EmploymentStatus, ClientDispositionType
from app.main.model.address import AddressType
from app.main.model.credit_report_account import CreditReportSignupStatus, CreditReportDataAccountType
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


class FrequencyTypeField(fields.String):
    def format(self, value):
        if isinstance(value, Frequency):
            return value.name
        else:
            return 'UNKNOWN'


class DateTimeFormatField(fields.String):
    def format(self, value):
        return value.strftime("%m-%d-%Y %H:%M")


class DateFormatField(fields.String):
    def format(self, value):
        return value.strftime("%m-%d-%Y")

# set the current address
class CurrentAddressField(fields.Raw):
    def format(self, records):
        result = { 'address': '', 'zip': '', 'city': '', 'state': ''}
        for addr in records:
            if addr.type == AddressType.CURRENT:
                result['address'] = addr.address1
                result['zip'] = addr.zip_code
                result['city'] = addr.city
                result['state'] = addr.state

        return result

class PreferedPhoneField(fields.Raw):
    def format(self, records):
        for record in records:
            cn = record.contact_number
            if cn is not None and cn.preferred is True:
                return cn.phone_number

        return ""


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


class ClientTypeField(fields.String):
    def format(self, value):
        if isinstance(value, ClientType):
            return value.name
        else:
            return 'UNKNOWN'


class FrequencyStatusField(fields.String):
    def format(self, value):
        if isinstance(value, FrequencyStatus):
            return value.name
        else:
            return 'UNKNOWN'

class ClientDispositionTypeField(fields.String):
    def format(self, value):
        if isinstance(value, ClientDispositionType):
            return value.name
        else:
            return 'UNKNOWN' 

class CandidateDispositionTypeField(fields.String):
    def format(self, value):
        if isinstance(value, CandidateDispositionType):
            return value.name
        else:
            return 'UNKNOWN' 

class ClientDispositionTypeField(fields.String):
    def format(self, value):
        if isinstance(value, ClientDispositionType):
            return value.name
        else:
            return 'UNKNOWN'


class CandidateDispositionTypeField(fields.String):
    def format(self, value):
        if isinstance(value, CandidateDispositionType):
            return value.name
        else:
            return 'UNKNOWN'

class CreditReportDataAccountTypeField(fields.String):
    def format(self, value):
        if isinstance(value, CreditReportDataAccountType):
            return value.name
        else:
            return 'UNKNOWN'

_credit_report_debt_model = {
    'debt_name': fields.String(required=True),
    'public_id': fields.String(required=False),
    'creditor': fields.String(required=True),
    'ecoa': fields.String(required=True),
    'account_number': fields.String(required=True),
    'account_type': CreditReportDataAccountTypeField(required=True),
    'push': fields.Boolean(required=True),
    'last_collector': fields.String(),
    'collector_account': fields.String(),
    'last_debt_status': fields.String(),
    'bureaus': fields.DateTime(),
    'days_delinquent': fields.Integer(required=True),
    'balance_original': fields.Float(required=True),
    'payment_amount': fields.Integer(),
    'credit_limit': fields.Integer(),
    'graduation': fields.DateTime(),
    'last_update': fields.DateTime()
}


class EmploymentStatusField(fields.String):
    def format(self, value):
        if isinstance(value, EmploymentStatus):
            return value.name
        else:
            return 'unknown'


class ClientDto:
    api = Namespace('clients', description='client related operations')
    client = api.model('client', {
        'first_name': fields.String(required=True, description='client first name'),
        'last_name': fields.String(required=True, description='client last name'),
        'email': fields.String(required=True, description='client email address'),
        'language': fields.String(required=True, enum=Language._member_names_),
        'phone': fields.String(required=True, description='client phone number'),
        'type': ClientTypeField(required=False, description='client type'),
        'public_id': fields.String(description='client identifier'),
    })
    update_client = api.model('update_client', {
        'first_name': fields.String(description='client first name'),
        'last_name': fields.String(description='client last name'),
        'email': fields.String(description='client email address'),
        'language': fields.String(enum=Language._member_names_),
        'phone': fields.String(description='client phone number'),
        'type': ClientTypeField(description='client type')
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
    client_dispositions = api.model('client_dispositions', {
        'select_type': ClientDispositionTypeField(),
        'name': fields.String(required=True),
        'value': fields.String(required=True)
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
    client_address = api.model('client_address', {
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'fromDate': fields.Date(required=True),
        'toDate': fields.Date(required=True),
        'type': AddressTypeField(required=True)
    })
    update_client_address = api.model('update_client_address', {
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'fromDate': fields.Date(required=True),
        'toDate': fields.Date(required=True),
        'type': AddressTypeField(required=True)
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

class CreditReportAccountStatusField(fields.String):
    def format(self, value):
        if isinstance(value, CreditReportSignupStatus):
            return value.name
        else:
            return 'unknown'

class LeadDto:
    api = Namespace('leads', description='lead related operations')
    credit_report_account = api.model('credit_report_account', {
        'public_id': fields.String(),
        'fico': fields.Integer(),
        'status': CreditReportAccountStatusField()
    })
    debt_payment_contract = api.model('debt_payment_contract', {
        'term': fields.Integer(),
        'payment_start_date': DateFormatField(),
        'commission_rate': fields.Float(),
        'sale_date': DateFormatField(),
    })
    user_account = api.model('users', {
        'id': fields.Integer(),
        'name': fields.String(attribute='full_name'),
    })
    bank_account = api.model('bank_accounts', {
        'bank_name': fields.String(),
        'account_number': fields.String(),
        'routing_number': fields.String(),
        'owner_name': fields.String(),
        'address': fields.String(),
        'city': fields.String(),
        'state': fields.String(),
        'ssn': fields.String(),
        'zip': fields.String(),
        'email': fields.String(),
    })
    lead = api.model('lead', {
        'public_id': fields.String(description='lead identifier'),
        'first_name': fields.String(required=True, description='lead first name'),
        'last_name': fields.String(required=True, description='lead last name'),
        'estimated_debt': fields.Integer(required=True, description='client estimated_debt'),
        'email': fields.String(required=True, description='lead email address'),
        'language': fields.String(required=True, enum=Language._member_names_),
        'ssn': fields.String(description='lead ssn'),
        'dob': DateFormatField(),
        # inserted_on is kept only for backward compatability
        'inserted_on': fields.DateTime(),
        'created_date': DateTimeFormatField(attribute='inserted_on'),
        'employment_status':EmploymentStatusField(),
        'disposition': fields.String(attribute='disposition.value'),
        'credit_report_account': fields.Nested(credit_report_account),
        'payment_contract': fields.Nested(debt_payment_contract),
        'modified_date': DateTimeFormatField(),
        'campaign_name': fields.String(description='campaign name'),
        'lead_source': fields.String(description='lead source'),
        'application_date': DateFormatField(),
        'bank_account': fields.Nested(bank_account),
        # use 'user_account' - if nested properties of user model is needed
        # for simplicity using only 'full_name' attribute
        'account_manager': fields.String(attribute='account_manager.full_name'),
        'team_manager': fields.String(attribute='team_manager.full_name'),
        'opener': fields.String(attribute='opener.full_name'),
        'address': CurrentAddressField(cls_or_instance='Address', attribute='addresses'),
        'phone': PreferedPhoneField(cls_or_instance='ClientContactNumber',attribute='contact_numbers')
    })
    lead_pagination=api.model('lead_pagination', {
        'page_number': fields.Integer(),
        'total_records': fields.Integer(),
        'limit': fields.Integer(),
        'data': fields.List(fields.Nested(lead))
    })
    update_lead = api.model('update_lead', {
        'first_name': fields.String(description='lead first name'),
        'last_name': fields.String(description='lead last name'),
        'estimated_debt': fields.Integer(description='client estimated_debt'),
        'email': fields.String(description='lead email address'),
        'dob': fields.DateTime(),
        'language': fields.String(enum=Language._member_names_),
        'phone': fields.String(description='lead phone number'),
        'type': ClientTypeField(description='client type')
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


class CandidateDto:
    api = Namespace('candidates', description='candidate related operations')
    credit_report_account = api.model('credit_report_account', {
        'public_id': fields.String(),
        'status': CreditReportAccountStatusField()
    })
    candidate_disposition = api.model('candidate_dispositions', {
        'value': fields.String(),
        'description': fields.String()
    })
    candidate = api.model('candidate', {
        'public_id': fields.String(),
        'prequal_number': fields.String(),
        'first_name': fields.String(),
        'last_name': fields.String(),
        'middle_initial': fields.String(),
        'suffix': fields.String(),
        'estimated_debt': fields.Integer(),
        'inserted_on': fields.DateTime(),
        'email': fields.String(),
        'dob': fields.Date(),
        'language': fields.String(enum=Language._member_names_),
        'status': CandidateStatusField(),
        'employment_status': EmploymentStatusField(),
        'campaign_name': fields.String(attribute='campaign.name'),
        'disposition': fields.String(attribute='disposition.value'),
        'credit_report_account': fields.Nested(credit_report_account),
        'address': CurrentAddressField(cls_or_instance='Address', attribute='addresses'),
        'phone': PreferedPhoneField(cls_or_instance='CandidateContactNumber',attribute='contact_numbers')
    })
    candidate_dispositions = api.model('candidate_disposition', {
        'select_type': CandidateDispositionTypeField(),
        'name': fields.String(required=True),
        'value': fields.String(required=True)
    })
    candidate_pagination=api.model('candidate_pagination', {
        'page_number': fields.Integer(),
        'total_number_of_records': fields.Integer(),
        'limit': fields.Integer(),
        'candidates': fields.List(fields.Nested(candidate))
    })
    update_candidate = api.model('update_candidate', {
        'first_name': fields.String(),
        'last_name': fields.String(),
        'middle_initial': fields.String(),
        'disposition': fields.String(),
        'suffix': fields.String(),
        'city': fields.String(),
        'state': fields.String(),
        'zip': fields.String(),
        'county': fields.String(),
        'email': fields.String(),
        'dob': fields.DateTime(),
        'language': fields.String(enum=Language._member_names_),
        'phone': fields.String(),
        'status': CandidateStatusField(),
        # 'employment_status': EmploymentStatusField(),

    })
    candidate_employment = api.model('candidate_employment', {
        'employer_name': fields.String(required=True),
        'start_date': fields.DateTime(required=True),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=False),
        'gross_salary_frequency': FrequencyStatusField(),
        'other_income': fields.Float(required=False),
        'other_income_frequency': FrequencyStatusField(required=False),
        'current': fields.Boolean(required=True, default=False)
    })

    update_candidate_employment = api.model('update_candidate_employment', {
        'employer_name': fields.String(required=True),
        'start_date': fields.DateTime(required=True),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=False),
        'gross_salary_frequency': FrequencyStatusField(required=False),
        'other_income': fields.Float(required=False),
        'other_income_frequency': FrequencyStatusField(required=False),
        'current': fields.Boolean(required=True, default=False)
    })
    candidate_address = api.model('candidate_address', {
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'from_date': fields.Date(required=True),
        'to_date': fields.Date(required=True),
        'type': AddressTypeField(required=True)
    })
    update_candidate_addresses = api.model('update_candidate_addresses', {
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'from_date': fields.Date(required=False),
        'to_date': fields.Date(required=False),
        'type': AddressTypeField(required=True)
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


class ConfigDto:
    api = Namespace('config', description='config related operations')
    contact_number_types = api.model('contact_number_types', {
        'id': fields.Integer(required=True),
        'name': fields.String(required=True),
        'description': fields.String(required=False),
        'inserted_on': fields.DateTime(required=True),
    })
    income_types = api.model('income_types', {
        'id': fields.Integer(required=True),
        'name': fields.String(required=True),
        'display_name': fields.String(required=True),
        'description': fields.String(required=False),
        'inserted_on': fields.DateTime(required=True),
    })
    expense_types = api.model('expense_types', {
        'id': fields.Integer(required=True),
        'name': fields.String(required=True),
        'display_name': fields.String(required=True),
        'description': fields.String(required=False),
        'inserted_on': fields.DateTime(required=True),
    })
    disposition = api.model('candidate_dispositions', {
        'public_id': fields.String(required=True),
        'inserted_on': fields.DateTime(required=True),
        'value': fields.String(required=False),
        'description': fields.String(required=False),
    })


class TestAPIDto:
    api = Namespace('tests', description='Test operations for Dev/QA')


class RemoteSignDto:
    api = Namespace('rsign', description='Remote signature related operations')

    docusign_template = api.model('docusign_template', {
        'id': fields.Integer(),
        'name': fields.String()
    })


class DebtPaymentDto:
    api = Namespace('debtpayment', description='Debt Payment related operations')
