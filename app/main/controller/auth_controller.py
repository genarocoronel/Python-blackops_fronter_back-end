from flask import request
from flask_restplus import Resource

from app.main.core.rac import RACMgr
from app.main.core.auth import Auth
from ..util.dto import AuthDto
from app.main.util.decorator import token_required

api = AuthDto.api
_user_auth = AuthDto.user_auth
_password_reset_req = AuthDto.password_reset_request
_validate_password_reset_req = AuthDto.validate_password_reset_request
_password_reset = AuthDto.password_reset


@api.route('/login')
class UserLogin(Resource):
    """
        User Login Resource
    """
    @api.doc('user login')
    @api.expect(_user_auth, validate=True)
    def post(self):
        # get the post data
        post_data = request.json
        return Auth.login_user(data=post_data)


@api.route('/refresh')
class UserLoginRefresh(Resource):
    """ Refreshes the Auth Token """
    @api.doc('user login refresh')
    @token_required
    def put(self):
        return Auth.refresh_token()


@api.route('/logout')
class LogoutAPI(Resource):
    """
    Logout Resource
    """
    @api.doc('logout a user')
    def post(self):
        # get auth token
        auth_header = request.headers.get('Authorization')
        return Auth.logout_user(data=auth_header)


@api.route('/password-reset')
class PasswordResetRequest(Resource):
    """ Password Reset """
    @api.doc('request password reset')
    @api.expect(_password_reset_req, validate=True)
    def post(self):
        post_data = request.json
        return Auth.request_reset_password(data=post_data)


@api.route('/password-reset/<reset_token>')
@api.param('reset_token', 'The User reset password token')
class PasswordReset(Resource):
    @api.doc('validate reset password request')
    @api.expect(_validate_password_reset_req, validate=True)
    def put(self, reset_token):
        post_data = request.json
        post_data.update(dict(reset_key=reset_token))
        return Auth.validate_reset_password_request(data=post_data)

    @api.doc('reset password')
    @api.expect(_password_reset, validate=True)
    def post(self, reset_token):
        post_data = request.json
        post_data.update(dict(reset_key=reset_token))
        return Auth.reset_password(data=post_data)

@api.route('/policies')
class AccessPolicies(Resource):
    @api.doc('Get access policies')
    def get(self):
        return RACMgr.get_access_policies()