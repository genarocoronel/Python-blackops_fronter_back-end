from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import MessageDto
from app.main.util.decorator import portal_token_required
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.service.portal_mssg_service import get_messages_for_portal_user, create_inbound_message
from flask import current_app as app


api = MessageDto.api
_message = MessageDto.message
_message_create = MessageDto.message_create

@api.route('')
class Message(Resource):
    @api.doc('Gets a list of Messages')
    @api.marshal_list_with(_message, envelope='data')
    @portal_token_required
    def get(self):
        """ Gets a list of Messages """
        mssgs = get_messages_for_portal_user()

        return mssgs, 200

    @api.doc('Crete a new Portal message on behalf of Portal User')
    @api.expect(_message_create, validate=False)
    @portal_token_required
    def post(self):
        """ Crete a new Portal message on behalf of Portal User """
        request_data = request.json
        content = request_data['content']
        result = create_inbound_message(content)
        return result, 200