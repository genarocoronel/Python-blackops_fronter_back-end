from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import AuthDto
from app.main.core.auth import Auth

api = AuthDto.api
_user_auth = AuthDto.user_auth


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
class LogoutAPI(Resource):
    """ Logs out a Portal User """
    @api.doc('logout a Portal User')
    def post(self):
        # get auth token
        auth_header = request.headers.get('Authorization')
        return Auth.logout_user(data=auth_header)