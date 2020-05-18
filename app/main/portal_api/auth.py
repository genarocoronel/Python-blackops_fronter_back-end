from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import AuthDto
from app.main.core.auth import Auth
from app.main.service.portal_user_service import invite_redeem

api = AuthDto.api
_user_auth = AuthDto.user_auth
_claim_invite = AuthDto.claim_invite


@api.route('/login')
class UserLogin(Resource):
    """ Portal User Login Resource """
    @api.doc('Portal User login')
    @api.expect(_user_auth, validate=True)
    def post(self):
        """ Logs in a Portal User """
        post_data = request.json
        return Auth.login_portal_user(data=post_data)


@api.route('/logout')
class UserLogoutAPI(Resource):
    """ Logs out a Portal User """
    @api.doc('logout a Portal User')
    def post(self):
        auth_header = request.headers.get('Authorization')
        return Auth.logout_user(data=auth_header)


@api.route('/claim/<invite_token>')
@api.param('invite_token', 'The invitation hash')
class ClaimAcc(Resource):
    """ Logs out a Portal User """
    @api.doc('logout a Portal User')
    @api.expect(_claim_invite, validate=False)
    def post(self, invite_token):
        post_data = request.json
        if invite_redeem(post_data['desired_password'], invite_token):
            response = {
                'success': True,
                'message': "Successfully claimed your Portal login. Please proceed to login."
            }
            return response, 200
        else:
            api.abort(400, message='Sorry: Could not validate that invitation token', success=False)