from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import DocDto
from app.main.util.decorator import portal_token_required
from app.main.service.docproc_service import get_docs_for_portal_user
from flask import current_app as app

api = DocDto.api
_doc = DocDto.doc

@api.route('')
class Doc(Resource):
    @api.doc('Gets a list of Docs')
    @api.marshal_list_with(_doc, envelope='data')
    @portal_token_required
    def get(self):
        """ Gets a list of Docs """
        docs = get_docs_for_portal_user()

        return docs, 200