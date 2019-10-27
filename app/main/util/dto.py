from flask_restplus import Namespace, fields
from app.main.model.client import ClientType
from app.main.util import parsers


class UserDto:
    api = Namespace('user', description='user related operations')
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
    api = Namespace('appointment', description='appointment related operations')
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
            return 'unknown'


class ClientDto:
    NAMESPACE = 'client'

    api = Namespace(NAMESPACE, description='client related operations')
    client = api.model(NAMESPACE, {
        'first_name': fields.String(required=True, description='client first name'),
        'last_name': fields.String(required=True, description='client last name'),
        'email': fields.String(required=True, description='client email address'),
        'language': fields.String(required=True, description='client language preference'),
        'phone': fields.String(required=True, description='client phone number'),
        'type': ClientTypeField(required=False, description='client type'),
        'public_id': fields.String(description='client identifier'),
    })


class LeadDto:
    NAMESPACE = 'lead'

    api = Namespace(NAMESPACE, description='lead related operations')
    lead = api.model(NAMESPACE, {
        'first_name': fields.String(required=True, description='lead first name'),
        'last_name': fields.String(required=True, description='lead last name'),
        'email': fields.String(required=True, description='lead email address'),
        'language': fields.String(required=True, description='lead language preference'),
        'phone': fields.String(required=True, description='lead phone number'),
        'type': ClientTypeField(required=False, description='client type'),
        'public_id': fields.String(description='lead identifier'),
    })
    lead_upload = parsers.file_upload
