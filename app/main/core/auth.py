import enum
import datetime
import jwt
import random
import uuid

from app.main import db
from app.main.config import key

from ..service.blacklist_service import save_token
from app.main.service.sms_service import sms_send_raw
from app.main.model.user import User, UserPasswordReset
from app.main.util.validate import is_email
from app.main.model.blacklist import BlacklistToken
from flask import current_app as app

class Auth():

    @staticmethod
    def login_user(data):
        """ Logs in a User for a given credential pair """
        try:
            user = User.query.filter_by(username=data.get('username')).first()
            if user and user.check_password(data.get('password')):
                auth_token = Auth.encode_auth_token(user.id)

                if auth_token:
                    # TODO: Implement 2-factor auth at a later time (per Keith & David on 2020-02-28)
                    # if user.require_2fa:
                    #     code = generate_code()
                    #     app.logger.debug(f'user authenticated with credentials; requires 2FA code: {code}')
                    #     sms_send_raw(user.personal_phone,
                    #                  f'{code} Use this code for Elite Doc Services. It will expire in 10 minutes',
                    #                  user.id)

                    response_object = {
                        'status': 'success',
                        'message': 'Successfully logged in.',
                        'user': {
                            'public_id': user.public_id,
                            'username': user.username,
                            'password': None,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'title': user.title,
                            'phone_number': user.personal_phone,
                            'language': user.language,
                            'personal_phone': user.personal_phone,                            
                            'last_4_of_phone': user.personal_phone[-4:],
                            'voip_route_number': user.voip_route_number,
                            'rac_role': user.role.name,
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
        """ Logs out an Authenticated User by invalidating current Auth Token """
        if data and ' ' in data:
            auth_token = data.split(" ")[1]
        elif data:
            auth_token = data
        else:
            auth_token = ''
        if auth_token:
            resp = Auth.decode_auth_token(auth_token)

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
        if auth_token and len(auth_token) > 0:
            resp = Auth.decode_auth_token(auth_token)

            if not isinstance(resp, str):
                user = User.query.filter_by(id=resp).first()
                response_object = {
                    'status': 'success',
                    'data': {
                        'public_id': user.public_id,
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'rac_role': user.role.name,
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
                # TODO: Finish implementing feature for sending SMS messages to Users of the CRM.
                # We may want to centralize SMS services via Bandwidth (or Jive?).
                # sms_send_raw(user.personal_phone,
                #              f'{code} Use this code for Elite Doc Services. It will expire in 10 minutes', user.id)
                response_object = {
                    'success': True,
                    'message': 'Password reset request successful',
                    'reset_key': reset_request.reset_key,
                    'phone_last_4': user.personal_phone[-4:]
                }
                return response_object, 201
            else:
                response_object = {
                    'success': False,
                    'message': 'No such user exist.'
                }
                return response_object, 403
        except Exception as e:
            print(e)
            response_object = {
                    'success': False,
                    'message': 'Failed Password Reset.'
            }
            return response_object, 404

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
    
    @staticmethod
    def encode_auth_token(user_id):
        """
        Generates an Auth Token for a Authenticated User
        :return: string
        """
        app.logger.info('Attempting encoding auth token')

        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                key,
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Decodes an Auth Token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, key)
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

    
    @staticmethod
    def generate_password(password_length=16):
        """ Generates a random Password """
        s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ@3_*"
        return ''.join(random.sample(s, password_length))

    def save_changes(*data):
        for entry in data:
            db.session.add(entry)
        db.session.commit()
    