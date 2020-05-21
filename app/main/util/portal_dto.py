from flask_restplus import Namespace, fields

from app.main.util import parsers
from app.main.model import Frequency

class FrequencyTypeField(fields.String):
    def format(self, value):
        if isinstance(value, Frequency):
            return value.name
        else:
            return 'UNKNOWN'

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
    claim_invite = api.model('claim_invite', {
        'desired_password': fields.String(required=True, description='The desired password to set for this account')
    })

class ConfigDto:
    api = Namespace('config', description="Config related operations")
    docproc_types = api.model('docproc_types', {
        'public_id': fields.String(required=True),
        'name': fields.String(required=True),
        'inserted_on': fields.DateTime(required=True),
        'updated_on': fields.DateTime(required=True),
    })

class DocDto:
    api = Namespace('docs', description='Doc related operations')
    doc_upload = parsers.doc_upload
    doc_type = api.model('doc_type', {
        'public_id': fields.String(required=False),
        'name': fields.String(required=False)
    })
    doc_user = api.model('doc_user', {
        'public_id': fields.String(required=False),
        'username': fields.String(required=False)
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
        'inserted_on': fields.DateTime(required=False),
        'updated_on': fields.DateTime(required=False)
    })
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

class MessageDto:
    api = Namespace('messages', description='Message related operations')
    message = api.model('message', {
        'public_id': fields.String(required=False),
        'portal_user_public_id': fields.String(required=False),
        'content': fields.String(required=False),
        'direction': fields.String(required=False),
        'author_public_id': fields.String(required=False),
        'author_name': fields.String(required=False),
        'is_viewed': fields.Boolean(required=False),
        'inserted_on': fields.DateTime(required=False)
    })
    message_create = api.model('message_create', {
        'content': fields.String(required=False)
    })

class BudgetDto:
    api = Namespace('budgets', description='Client Budget related operations')
    income_source = api.model('client_income', {
        'income_type_id': fields.Integer(required=True),
        'income_type': fields.String(required=True),
        'value': fields.Integer(required=True),
        'frequency': FrequencyTypeField(required=True),
    })
    monthly_expense = api.model('client_monthly_expense', {
        'expense_type_id': fields.Integer(required=True),
        'expense_type': fields.String(required=True),
        'value': fields.Integer(required=True),
    })

class AppointmentDto:
    api = Namespace('appointments', description='Client Appointments related operations')
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

class CallsheetDto:
    api = Namespace('callsheets', description='Callsheet related operations')
    callsheet = api.model('callsheet', {
        'public_id': fields.String(required=False, description='The Callsheet public ID'),
        'callsheet_date': fields.DateTime(required=True, description='Date of receiving a call from collection company'),
        'is_orig_creditor': fields.Boolean(required=True, description='Flag indicating whether caller was original creditor'),
        'is_hardship_call': fields.Boolean(required=True, description='Flag indicating if this was a hardship call. Default false.'),
        'debt_name': fields.String(required=True, description='The name of the debt'),
        'creditor_name': fields.String(required=True, description='The name of the creditor'),
        'collector_name': fields.String(required=True, description='The name of the collector'),
        'received_from_phone_number': fields.String(required=True, description='The phone number from which call originated'),
        'received_on_phone_type': fields.String(required=True, description='The Client phone type receiving collecotr call. Valid values: cell, home, work'),
        'notes': fields.String(required=False, description='Optional Notes, if any'),
        'is_file_attached': fields.Boolean(required=False, description='Flag indicating if a file was attached with Callsheet. Default false'),
        'inserted_on': fields.DateTime(required=False),
        'updated_on': fields.DateTime(required=False)
    })
    callsheet_create = api.model('callsheet_create', {
        'callsheet_date': fields.DateTime(required=True, description='Date of receiving a call from collection company'),
        'is_orig_creditor': fields.Boolean(required=True, description='Flag indicating whether caller was original creditor'),
        'is_hardship_call': fields.Boolean(required=True, description='Flag indicating if this was a hardship call. Default false.'),
        'debt_name': fields.String(required=True, description='The name of the debt'),
        'creditor_name': fields.String(required=True, description='The name of the creditor'),
        'collector_name': fields.String(required=True, description='The name of the collector'),
        'received_from_phone_number': fields.String(required=True, description='The phone number from which call originated'),
        'received_on_phone_type': fields.String(required=True, description='The Client phone type receiving collecotr call. Valid values: cell, home, work'),
        'notes': fields.String(required=False, description='Optional Notes, if any')
    })