import datetime
import random
import uuid

from app.main.model.user import User, UserPasswordReset
from app.main.service.sms_service import sms_send_raw
from app.main.service.user_service import save_changes
from app.main.util.validate import is_email
from flask import current_app as app

from ..service.blacklist_service import save_token


def generate_code():
    return str(random.randrange(100000, 999999))


class Auth:

    @staticmethod
    def generate_password(password_length=16):
        s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ@3_*"
        return ''.join(random.sample(s, password_length))

    @staticmethod
    def login_user(data):
        try:
            user = User.query.filter_by(username=data.get('username')).first()
            if user and user.check_password(data.get('password')):
                auth_token = user.encode_auth_token(user.id)
                if auth_token:
                    if user.require_2fa:
                        code = generate_code()
                        app.logger.debug(f'user authenticated with credentials; requires 2FA code: {code}')
                        sms_send_raw(user.personal_phone,
                                     f'{code} Use this code for Elite Doc Services. It will expire in 10 minutes',
                                     user.id)

                    response_object = {
                        'status': 'success',
                        'message': 'Successfully logged in.',
                        'user': {
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'title': user.title,
                            'last_4_of_phone': user.personal_phone[-4:],
                            'require_2fa': user.require_2fa,
                            'token': auth_token.decode()
                        }
                    }
                    return response_object, 200
            else:
                response_object = {
                    'status': 'fail',
                    'message': 'username or password does not match.'
                }
                return response_object, 401

        except Exception as e:
            print(e)
            response_object = {
                'status': 'fail',
                'message': 'Try again'
            }
            return response_object, 500

    @staticmethod
    def logout_user(data):
        if data:
            auth_token = data.split(" ")[1]
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                # mark the token as blacklisted
                return save_token(token=auth_token)
            else:
                response_object = {
                    'status': 'fail',
                    'message': resp
                }
                return response_object, 401
        else:
            response_object = {
                'status': 'fail',
                'message': 'Provide a valid auth token.'
            }
            return response_object, 403

    @staticmethod
    def get_logged_in_user(new_request):
        # get the auth token
        auth_token = new_request.headers.get('Authorization')
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                user = User.query.filter_by(id=resp).first()
                response_object = {
                    'status': 'success',
                    'data': {
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'admin': user.admin,
                        'registered_on': str(user.registered_on)
                    }
                }
                return response_object, 200
            response_object = {
                'status': 'fail',
                'message': resp
            }
            return response_object, 401
        else:
            response_object = {
                'status': 'fail',
                'message': 'Provide a valid auth token.'
            }
            return response_object, 401

    @staticmethod
    def request_reset_password(data):
        try:
            query_value = data.get('query')

            if is_email(query_value):
                user = User.query.filter_by(email=query_value).first()
            else:
                user = User.query.filter_by(personal_phone=query_value).first()
                if user is None:
                    user = User.query.filter_by(username=query_value).first()

            if user:
                code = generate_code()
                reset_request = UserPasswordReset(
                    reset_key=str(uuid.uuid4()),
                    code=code,
                    user=user
                )
                save_changes(reset_request)
                app.logger.info('Sending password reset email...')
                app.logger.debug(f'password reset request id: {reset_request.reset_key}, code: {code}')
                sms_send_raw(user.personal_phone,
                             f'{code} Use this code for Elite Doc Services. It will expire in 10 minutes', user.id)

                response_object = {
                    'success': True,
                    'message': 'Password reset request successful',
                    'reset_key': reset_request.reset_key,
                    'phone_last_4': user.personal_phone[-4:]
                }
                return response_object, 201
        except Exception as e:
            print(e)

    @staticmethod
    def validate_reset_password_request(data):
        password_reset = UserPasswordReset.query.filter_by(
            reset_key=data['reset_key']).first()  # type: UserPasswordReset

        if password_reset:
            if not password_reset.is_expired():
                if password_reset.check_code(data['code']):
                    password_reset.validated = True
                    save_changes(password_reset)
                    response_object = {
                        'success': True,
                        'message': 'Successfully validated password reset request'
                    }
                    return response_object, 200
                else:
                    response_object = {
                        'success': False,
                        'message': 'Failed to validate password reset request'
                    }
                    return response_object, 403
            else:
                response_object = {
                    'message': 'Password reset request has expired.'
                }
                return response_object, 410
        else:
            response_object = {
                'message': 'Invalid password reset request'
            }
            return response_object, 404

    @staticmethod
    def reset_password(data):
        password_reset = UserPasswordReset.query.filter_by(
            reset_key=data['reset_key']).first()  # type: UserPasswordReset

        if password_reset:
            if not password_reset.is_expired():
                if not password_reset.validated:
                    response_object = {
                        'message': 'Please validate password reset request with code'
                    }
                    return response_object, 410
                else:
                    user = password_reset.user
                    user.password = data['password']
                    password_reset.has_activated = True
                    save_changes(password_reset, user)
                    response_object = {
                        'success': True,
                        'message': 'Password reset successful'
                    }
                    return response_object, 200
            else:
                response_object = {
                    'message': 'Password reset request has expired.'
                }
                return response_object, 410

        else:
            response_object = {
                'message': 'Invalid password reset request'
            }
            return response_object, 404
