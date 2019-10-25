import datetime
import uuid

from app.main.model.user import User, UserPasswordReset
from app.main.service.user_service import save_changes
from app.main.util.validate import is_email
from flask import current_app as app
from ..service.blacklist_service import save_token


class Auth:

    @staticmethod
    def login_user(data):
        try:
            user = User.query.filter_by(username=data.get('username')).first()
            if user and user.check_password(data.get('password')):
                auth_token = user.encode_auth_token(user.id)
                if auth_token:
                    response_object = {
                        'status': 'success',
                        'message': 'Successfully logged in.',
                        'user': {
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'title': user.title,
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
                reset_request = UserPasswordReset(
                    reset_key=str(uuid.uuid4()),
                    user=user
                )
                save_changes(reset_request)
                # TODO: initiate password reset for user
                app.logger.info('Sending password reset email...')
                app.logger.debug(f'password reset request id: {reset_request.reset_key}')

                response_object = {
                    'success': True,
                    'message': 'Password reset request successful'
                }
                return response_object, 201
        except Exception as e:
            print(e)

    @staticmethod
    def reset_password(data):
        password_reset = UserPasswordReset.query.filter_by(reset_key=data['reset_key']).first()  # type: UserPasswordReset
        if password_reset:
            now = datetime.datetime.utcnow()
            duration = now - password_reset.datetime

            # password reset expires in 24 hours / 1 day
            if not password_reset.has_activated and duration.days <= 1:
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
