from flask_restplus import Namespace, fields


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

class DocDto:
    api = Namespace('docs', description='Doc related operations')
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