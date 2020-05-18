from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import CallsheetDto
from app.main.util.decorator import portal_token_required
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.service.portal_callsheet_service import get_callsheets_for_portal_user, create_callsheet
from flask import current_app as app


api = CallsheetDto.api
_callsheet = CallsheetDto.callsheet
_callsheet_create = CallsheetDto.callsheet_create

@api.route('')
class Callsheet(Resource):
    @api.doc('Gets a list of Callsheets')
    @api.marshal_list_with(_callsheet, envelope='data')
    @portal_token_required
    def get(self):
        """ Gets a list of Callsheets """
        mssgs = get_callsheets_for_portal_user()
        return mssgs, 200

    @api.doc('Crete a new Portal Callsheets on behalf of Portal User')
    @api.expect(_callsheet_create, validate=False)
    @portal_token_required
    def post(self):
        """ Crete a new Portal Callsheets on behalf of Portal User """
        request_data = request.json
        result = create_callsheet(request_data)
        return result, 200