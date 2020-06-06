import os

from flask_restplus import Namespace, fields

from app.main.model import Language, Frequency
from app.main.model.candidate import CandidateImportStatus, CandidateStatus, CandidateDispositionType
from app.main.model.employment import FrequencyStatus
from app.main.model.client import Client, ClientType, EmploymentStatus, ClientDispositionType
from app.main.model.address import AddressType
from app.main.model.credit_report_account import CreditReportSignupStatus, CreditReportDataAccountType
from app.main.model.pbx import VoiceCommunicationType, CommunicationType
from app.main.model.user import User
from app.main.core.auth import Auth
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


class CommsTypeField(fields.String):
    def format(self, value):
        if isinstance(value, CommunicationType):
            return value.name


class DateTimeFormatField(fields.String):
    def format(self, value):
        return value.strftime("%m-%d-%Y %H:%M")


class DateFormatField(fields.String):
    def format(self, value):
        return value.strftime("%m-%d-%Y")

## temp
from datetime import timedelta
class ScheduleEndField(fields.String):
    def format(self, value):
        result = value + timedelta(hours=1)
        return result.strftime("%m-%d-%Y %H:%M")


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


class FullNameField(fields.String):
    def format(self, value):
        if isinstance(value, User):
            return '{} {}'.format(value.first_name, value.last_name)
        elif isinstance(value, Client):
            return '{} {}'.format(value.first_name, value.last_name)
        else:
            return ''


authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}


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
    rac_role = api.model('rac_role', {
        'value': fields.String(required=False)
    })
    new_user = api.model('new_user', {
        'email': fields.String(required=True, description='user email address'),
        'username': fields.String(required=True, description='user username'),
        'password': fields.String(required=True, description='user password', example=Auth.generate_password()),
        'first_name': fields.String(required=True, description='user first name'),
        'last_name': fields.String(required=True, description='user last name'),
        'title': fields.String(required=True, description='user title', example='Opener Rep'),
        'rac_role': fields.Nested(rac_role),
        'language': fields.String(required=True, description='user language preference', example='en'),
        'personal_phone': fields.String(required=True, description='user personal phone number'),
        'voip_route_number': fields.String(required=False, description='user VOIP routing number')

    })
    update_user = api.model('update_user', {
        'email': fields.String(required=False, description='user email address'),
        'first_name': fields.String(required=False, description='user first name'),
        'last_name': fields.String(required=False, description='user last name'),
        'title': fields.String(required=False, description='user title', example='Opener Rep'),
        'language': fields.String(required=False, description='user language preference', example='en'),
        'personal_phone': fields.String(required=False, description='user personal phone number'),
        'voip_route_number': fields.String(required=False, description='user VOIP routing number')

    })
    user = api.model('user', {
        'public_id': fields.String(description='user identifier'),
        'username': fields.String(required=True, description='user username'),
        'email': fields.String(required=True, description='user email address'),
        'first_name': fields.String(required=True, description='user first name'),
        'last_name': fields.String(required=True, description='user last name'),
        'title': fields.String(required=True, description='user title'),
        'language': fields.String(required=True, description='user language preference'),
        'phone_number': fields.String(required=True, description='user phone number'),
        'personal_phone': fields.String(required=True, description='user personal phone number'),
        'last_4_of_phone': fields.String(required=True, description='Last 4 of user personal phone number'),
        'voip_route_number': fields.String(required=False, description='user VOIP routing number'),
        'rac_role': fields.String(required=False, description='RAC Role'),
        'department': fields.String(required=False, description='user department'),
    })
    user_supressed = api.model('user_supressed', {
        'public_id': fields.String(description='user identifier'),
        'username': fields.String(required=True, description='user username'),
        'first_name': fields.String(required=True, description='user first name'),
        'last_name': fields.String(required=True, description='user last name'),
        'voip_route_number': fields.String(required=False, description='user VOIP routing number'),
        'rac_role': fields.String(required=False, description='RAC Role')
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
    rac_roles = api.model('rac_role', {
        'id': fields.String(required=False),
        'name': fields.String(required=True, example='opener_rep'),
        'name_friendly': fields.String(required=False, example='Opener Rep'),
        'description': fields.String(required=True, example='Opener Rep Role'),
        'inserted_on': fields.DateTime(required=False),
        'updated_on': fields.DateTime(required=False),
    })


class AppointmentDto:
    api = Namespace('appointments', description='appointment related operations')
    client = api.model('clients', {
        'public_id': fields.String(attribute='public_id'),
        'name': fields.String(attribute='full_name'),
        'disposition': fields.String(attribute='disposition.value')
    })
    user = api.model('users', {
        'public_id': fields.String(attribute='public_id'),
        'name': fields.String(attribute='full_name'),
    })
    appointment = api.model('appointment', {
        'public_id': fields.String(),
        'client': fields.Nested(client),
        'agent': fields.Nested(user),
        'scheduled_at': DateTimeFormatField(attribute='scheduled_at'),
        'end_at': ScheduleEndField(attribute='scheduled_at'),
        'summary': fields.String(required=True, description='summary of appointment'),
        'location': fields.String(),
        'reminder_types': fields.String(required=True, description='type(s) of reminders to be sent to client'),
        'status': fields.String(description='status of appointment'),
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
    'account_type': fields.String(required=True),
    'push': fields.Boolean(required=True),
    'collector_account': fields.String(attribute='debt_collector.name'),
    'last_collector': fields.String(attribute='prev_debt_collector.name'),
    'collector_ref_no': fields.String(),
    'last_debt_status': fields.String(),
    'bureaus': fields.DateTime(),
    'days_delinquent': fields.Integer(required=True),
    'balance_original': fields.Float(required=True),
    'payment_amount': fields.Integer(),
    'credit_limit': fields.Integer(),
    'graduation': fields.DateTime(),
    'last_update': fields.DateTime(),
    'client_id': fields.Integer(attribute='credit_report_account.client_id'),
}

_communication = {
    'public_id': fields.String(required=True),
    'type': CommsTypeField(required=True),
    'source_number': fields.Integer(required=True),
    'destination_number': fields.Integer(required=False),
    'outside_number': fields.Integer(required=False),
    'receive_date': fields.DateTime(required=True),
    'body_text': fields.String(required=False),
    'duration_seconds': fields.Integer(required=False),
    'file_size_bytes': fields.Integer(required=False),
    'file_bucket_name': fields.String(required=False),
    'file_bucket_key': fields.String(required=False),
    'inserted_on': fields.DateTime(required=True),
    'is_viewed': fields.Boolean(required=True),
}


class EmploymentStatusField(fields.String):
    def format(self, value):
        if isinstance(value, EmploymentStatus):
            return value.name
        else:
            return 'unknown'


class CreditReportAccountStatusField(fields.String):
    def format(self, value):
        if isinstance(value, CreditReportSignupStatus):
            return value.name
        else:
            return 'unknown'

class ClientDto:
    api = Namespace('clients', description='client related operations')
    credit_report_account = api.model('credit_report_account', {
        'public_id': fields.String(),
        'status': CreditReportAccountStatusField()
    })
    client = api.model('client', {
        'first_name': fields.String(required=True, description='client first name'),
        'last_name': fields.String(required=True, description='client last name'),
        'email': fields.String(required=True, description='client email address'),
        'language': fields.String(required=True, enum=Language._member_names_),
        'phone': fields.String(required=True, description='client phone number'),
        'type': ClientTypeField(required=False, description='client type'),
        'public_id': fields.String(description='client identifier'),
        'credit_report_account': fields.Nested(credit_report_account),
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
        'employer_name': fields.String(required=True),
        'start_date': fields.DateTime(required=True),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=False),
        'gross_salary_frequency': FrequencyStatusField(),
        'other_income': fields.Float(required=False),
        'other_income_frequency': FrequencyStatusField(required=False),
        'current': fields.Boolean(required=True, default=False)
    })
    update_client_employment = api.model('update_client_employment', {
        'employer_name': fields.String(required=True),
        'start_date': fields.DateTime(),
        'end_date': fields.DateTime(),
        'gross_salary': fields.Float(required=False),
        'gross_salary_frequency': FrequencyStatusField(required=False),
        'other_income': fields.Float(required=False),
        'other_income_frequency': FrequencyStatusField(required=False),
        'current': fields.Boolean(required=True, default=False)
    })
    client_dispositions = api.model('client_dispositions', {
        'select_type': ClientDispositionTypeField(),
        'name': fields.String(required=True),
        'value': fields.String(required=True)
    })
    client_address = api.model('client_address', {
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'from_date': fields.Date(required=True, source="from_date"),
        'to_date': fields.Date(required=True, source="to_date"),
        'type': AddressTypeField(required=True)
    })
    update_client_address = api.model('update_client_address', {
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'from_date': fields.Date(required=True, source="from_date"),
        'to_date': fields.Date(required=True, source="to_date"),
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
    contact_number = api.model('contact_number', {
        'phone_type_id': fields.Integer(required=True),
        'phone_type': fields.String(required=True),
        'phone_number': fields.String(required=True),
        'preferred': fields.Boolean(required=True, default=False)
    })
    update_contact_number = api.model('update_contact_number', {
        'phone_type_id': fields.Integer(required=True),
        'phone_number': fields.String(required=True),
        'preferred': fields.Boolean(required=True, default=False)
    })
    new_credit_report_account = api.model('coclient_create_request', {
        'first_name': fields.String(required=True, example='Charlie'),
        'last_name': fields.String(required=True, example='Test-PJNDL'),
        'zip': fields.String(required=True, example='01001'),
        'phone': fields.String(required=True, example='555-555-5555')
    })
    update_credit_report_account = api.model('coclient_update_request', {
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
    communication = api.model('communication', _communication)
    doc_user = api.model('doc_user', {
        'public_id': fields.String(required=False),
        'username': fields.String(required=False)
    })
    doc_type = api.model('doc_type', {
        'public_id': fields.String(required=False),
        'name': fields.String(required=False)
    })
    doc_note = api.model('doc_note', {
        'public_id': fields.String(required=False),
        'content': fields.String(required=False),
        'author': fields.Nested(doc_user),
        'inserted_on': fields.DateTime(required=False),
        'updated_on': fields.DateTime(required=False),
    })
    doc_note_create = api.model('doc_note_create', {
        'content': fields.String(required=True, example='This is a cool note for this Doc')
    })
    doc_upload = parsers.doc_upload
    doc = api.model('doc', {
        'public_id': fields.String(required=False),
        'file_name': fields.String(required=False),
        'doc_name': fields.String(required=False),
        'source_channel': fields.String(required=False),
        'type': fields.Nested(doc_type),
        'correspondence_date': fields.String(required=False),
        'from_who': fields.String(required=False),
        'debt_name': fields.String(required=False),
        'creditor_name': fields.String(required=False),
        'collector_name': fields.String(required=False),
        'status': fields.String(required=False),
        'is_published': fields.Boolean(required=False),
        'notes': fields.List(fields.Nested(doc_note)),
        'inserted_on': fields.DateTime(required=False),
        'created_by_username': fields.String(required=False),
        'updated_on': fields.DateTime(required=False),
        'updated_by_username': fields.String(required=False),
    })
    doc_create = api.model('doc_create', {
        'source_channel': fields.String(required=False, example='One of: Mail, Fax, SMS, Email'),
        'doc_name': fields.String(required=True, example='CITI Collection Letter'),
        'type': fields.Nested(doc_type),
        'correspondence_date': fields.String(required=False, example='2020-04-15'),
        'from_who': fields.String(required=False, example='Some Collection Firm'),
        'debt_name': fields.String(required=False, example='ZYZ Bank Visa'),
        'creditor_name': fields.String(required=False, example='ZYZ Bank'),
        'collector_name': fields.String(required=False, example='Zoo, Collection Firm')
    })
    doc_update = api.model('doc_update', {
        'doc_name': fields.String(required=False),
        'type': fields.Nested(doc_type),
        'correspondence_date': fields.String(required=False, example='2020-04-15'),
        'from_who': fields.String(required=False, example='Zoo, Collection Firm'),
        'debt_name': fields.String(required=False, example='ZYZ Bank Visa'),
        'creditor_name': fields.String(required=False, example='ZYZ Bank'),
        'collector_name': fields.String(required=False, example='Zoo, Collection Firm'),
        'status': fields.String(required=False),
        'is_published': fields.Boolean(required=False)
    })


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
    notification_preference = api.model('notification_preferences', {
        'service_call': fields.String(attribute='service_call.name'),
        'appt_reminder': fields.String(attribute='appt_reminder.name'),
        'doc_notification': fields.String(attribute='doc_notification.name'),
        'payment_reminder': fields.String(attribute='payment_reminder.name'),
    })
    lead = api.model('lead', {
        'public_id': fields.String(description='lead identifier'),
        'first_name': fields.String(required=True, description='lead first name'),
        'last_name': fields.String(required=True, description='lead last name'),
        'middle_initial': fields.String(),
        'email': fields.String(required=True, description='lead email address'),
        'language': fields.String(required=True, enum=Language._member_names_),
        'estimated_debt': fields.Integer(description='client estimated_debt'),
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
        'co_client_id': fields.Integer(attribute='co_client.id'),
        # use 'user_account' - if nested properties of user model is needed
        # for simplicity using only 'full_name' attribute
        'account_manager': fields.String(attribute='account_manager.full_name'),
        'team_manager': fields.String(attribute='team_manager.full_name'),
        'opener': fields.String(attribute='opener.full_name'),
        'address': CurrentAddressField(cls_or_instance='Address', attribute='addresses'),
        'phone': PreferedPhoneField(cls_or_instance='ClientContactNumber',attribute='contact_numbers'),
        'notification_pref': fields.Nested(notification_preference),
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
        'dob': DateFormatField(),
        'language': fields.String(enum=Language._member_names_),
        'phone': fields.String(description='lead phone number'),
        'type': ClientTypeField(description='client type')
    })
    lead_address = api.model('lead_address', {
        'address1': fields.String(required=True),
        'address2': fields.String(required=False),
        'zip_code': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'from_date': fields.Date(required=True, source="from_date"),
        'to_date': fields.Date(required=True, source="to_date"),
        'type': AddressTypeField(required=True)
    })
    contact_number = api.model('contact_number', {
        'phone_type_id': fields.Integer(required=True, attribute="contact_number_type_id"),
        'phone_type': fields.String(required=True, attribute="contact_number_type.name"),
        'phone_number': fields.String(required=True),
        'preferred': fields.Boolean(required=True, default=False)
    })
    lead_phone = api.model('lead_phone', {
        'contact_number': fields.Nested(contact_number),
    })
    co_client = api.model('co_client', {
        'first_name': fields.String(description='lead first name'),
        'last_name': fields.String(description='lead last name'),
        'public_id': fields.String(),
        'middle_initial': fields.String(),
        'email': fields.String(description='lead email address'),
        'dob': DateFormatField(),
        'ssn': fields.String(),
        'estimated_debt': fields.Integer(description='client estimated_debt'),
        'language': fields.String(required=True, enum=Language._member_names_),
        'employment_status': fields.String(),
        'contact_numbers': fields.List(fields.Nested(lead_phone)),
        'addresses': fields.List(fields.Nested(lead_address)),
        'credit_report_account': fields.Nested(credit_report_account),
        'notification_pref': fields.Nested(notification_preference),
    })

    credit_report_debt = api.model('credit_report_debt', _credit_report_debt_model)
    new_credit_report_account = api.model('lead_create_request', {
        'first_name': fields.String(required=True, example='Charlie'),
        'last_name': fields.String(required=True, example='Test-PJNDL'),
        'zip': fields.String(required=True, example='01001'),
        'phone': fields.String(required=True, example='555-555-5555')
    })
    update_credit_report_account = api.model('lead_update_request', {
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

    debt_payment_contract = api.model('debt_payment_contract', {
        'monthly_fee': fields.Float(),
    })

    debt_payment_schedule = api.model('debt_payment_schedule', {
        'due_date': DateFormatField(),
        'amount': fields.Float(),
        'status': fields.String(attribute='status.name'),
        'contract': fields.Nested(debt_payment_contract),
    })
    communication = api.model('communication', _communication)


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
        'fico': fields.Integer(),
        'status': CreditReportAccountStatusField()
    })
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
    candidate_communication = api.model('communication', _communication)


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
    docproc_types = api.model('docproc_types', {
        'public_id': fields.String(required=True),
        'name': fields.String(required=True),
        'inserted_on': fields.DateTime(required=True),
        'updated_on': fields.DateTime(required=True),
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


class NotesDto:
    api = Namespace('notes', description='note related operations')
    note = api.model('note', {
        'candidate_id': fields.String(required=False, description='identifier for candidate'),
        'client_id': fields.String(required=False, description='identifier for client'),
        'content': fields.String(required=True)
    })


class CommunicationDto:
    api = Namespace('communications', description='Communication related operations')
    communication = api.model('communication', _communication)


class SmsDto:
    api = Namespace('sms', description='SMS related operations')

    new_sms_mssg_registration = api.model('sms_message_create_request', {
        'time': fields.String(required=False, example='2020-02-18T18:38:38.620Z'),
        'type': fields.String(required=False, example='message-received'),
        'to': fields.String(required=False, example='+15554443333'),
        'description': fields.String(required=False, example='Incoming message received'),
        'message': fields.String(required=False, example='a Provider message object'),

    })


class CollectorDto:
    api = Namespace('collectors', description='')

    collector = api.model('collector', {
        'public_id': fields.String(required=False),
        'name': fields.String(required=False),
        'phone': fields.String(required=False),
        'fax': fields.String(required=False),
        'address': fields.String(required=False),
        'city': fields.String(required=False),
        'state': fields.String(required=False),
        'zip_code': fields.String(required=False),
    })
    collector_create = api.model('doc_create', {
        'name': fields.String(required=True),
        'phone': fields.String(required=False),
        'fax': fields.String(required=False),
        'address': fields.String(required=True),
        'city': fields.String(required=True),
        'state': fields.String(required=True),
        'zip_code': fields.String(required=False),
    })

class DocprocDto:
    api = Namespace('docproc', description='Doc Process related operations')
    doc_type = api.model('doc_type', {
        'public_id': fields.String(required=False),
        'name': fields.String(required=False)
    })
    doc_user = api.model('doc_user', {
        'public_id': fields.String(required=False),
        'username': fields.String(required=False)
    })
    doc_client = api.model('doc_client', {
        'public_id': fields.String(required=False),
        'first_name': fields.String(required=False),
        'last_name': fields.String(required=False),
        'status':  fields.String(required=False),
    })
    doc_note = api.model('doc_note', {
        'public_id': fields.String(required=False),
        'content': fields.String(required=False),
        'author': fields.Nested(doc_user),
        'inserted_on': fields.DateTime(required=False),
        'updated_on': fields.DateTime(required=False),
    })
    doc = api.model('doc', {
        'public_id': fields.String(required=False),
        'file_name': fields.String(required=False),
        'doc_name': fields.String(required=False),
        'source_channel': fields.String(required=False),
        'type': fields.Nested(doc_type),
        'correspondence_date': fields.String(required=False),
        'from_who': fields.String(required=False),
        'debt_name': fields.String(required=False),
        'creditor_name': fields.String(required=False),
        'collector_name': fields.String(required=False),
        'status': fields.String(required=False),
        'is_published': fields.Boolean(required=False),
        'notes': fields.List(fields.Nested(doc_note)),
        'client': fields.Nested(doc_client),
        'docproc_user': fields.Nested(doc_user),
        'accmgr_user': fields.Nested(doc_user),
        'inserted_on': fields.DateTime(required=False),
        'created_by_username': fields.String(required=False),
        'updated_on': fields.DateTime(required=False),
        'updated_by_username': fields.String(required=False),
    })
    doc_assign = api.model('doc_assign', {
        'public_id': fields.String(required=True, example='Doc public ID such as 39seeae5-c0a3-4de7-8df0-0c6532a07j41'),
    })
    doc_multiassignment = api.model('doc_multiassignment', {
        'assignee_public_id': fields.String(required=True, example='User ID such as c5feeae5-c0a3-4de7-8df0-0c6532a07d74'),
        'docs': fields.List(fields.Nested(doc_assign))
    })
    doc_update = api.model('doc_update', {
        'doc_name': fields.String(required=False),
        'type': fields.Nested(doc_type),
        'correspondence_date': fields.String(required=False, example='2020-04-15'),
        'from_who': fields.String(required=False, example='Zoo, Collection Firm'),
        'debt_name': fields.String(required=False, example='ZYZ Bank Visa'),
        'creditor_name': fields.String(required=False, example='ZYZ Bank'),
        'collector_name': fields.String(required=False, example='Zoo, Collection Firm'),
        'status': fields.String(required=False),
        'is_published': fields.Boolean(required=False)
    })
    doc_move = api.model('doc_move', {
        'public_id': fields.String(required=True, example='Client ID such as c5feeae5-c0a3-4de7-8df0-0c6532a07d74')
    })
    doc_note_create = api.model('doc_note_create', {
        'content': fields.String(required=True, example='This is a cool note for this Doc')
    })
    doc_upload = parsers.doc_upload
    doc_create = api.model('doc_create', {
        'source_channel': fields.String(required=False, example='One of: Mail, Fax, SMS, Email, Portal'),
        'doc_name': fields.String(required=True, example='CITI Collection Letter'),
        'type': fields.Nested(doc_type),
        'correspondence_date': fields.String(required=False, example='2020-04-15'),
        'from_who': fields.String(required=False, example='Some Collection Firm'),
        'debt_name': fields.String(required=False, example='ZYZ Bank Visa'),
        'creditor_name': fields.String(required=False, example='ZYZ Bank'),
        'collector_name': fields.String(required=False, example='Zoo, Collection Firm')
    })


class TeamDto:
    api = Namespace('teams', description='Team Request related operations')

    client = api.model('clients', {
        'id': fields.String(attribute='public_id'),
        'name': fields.String(attribute='full_name'),
        'disposition': fields.String(attribute='disposition.value')
    })

    contract = api.model('debt_payment_contract', {
        'id': fields.Integer(),
        'term': fields.Integer(),
        'monthly_fee': fields.Float(),
        'total_paid': fields.Float(),
        'num_term_paid': fields.Integer(attribute='num_inst_completed'),
        'client': fields.Nested(client),
    })

    revision = api.model('debt_payment_contract_revision', {
        'method': fields.String(attribute='method.name'),
    })

    team_request = api.model('team_requests', {
        'id': fields.String(attribute='public_id'),
        'requested_on': DateTimeFormatField(),
        'account_manager': fields.String(attribute='team_manager.full_name'),
        'team_manager': fields.String(attribute='team_manager.full_name'),
        'req_type': fields.String(attribute='request_type.title'),
        'description': fields.String(),
        'status': fields.String(attribute='status.name'),
        'contract': fields.Nested(contract),
        'revision': fields.Nested(revision),
    });


class TaskDto:
    api = Namespace('tasks', description='User Task related operations')

    client = api.model('clients', {
        'id': fields.String(attribute='public_id'),
        'name': fields.String(attribute='full_name'),
        'disposition': fields.String(attribute='disposition.value')
    })

    user_task = api.model('user_tasks', {
        'id': fields.Integer(),
        'title': fields.String(),
        'description': fields.String(),
        'requested_on': DateTimeFormatField(),
        'priority': fields.String(attribute='priority'),
        'status': fields.String(attribute='status'),
        'client': fields.Nested(client),
        'due_date': DateTimeFormatField(),
        'inserted_on': DateTimeFormatField(),
    });
