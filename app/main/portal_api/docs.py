from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import DocDto
from app.main.util.decorator import portal_token_required
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.service.docproc_service import get_docs_for_portal_user, get_doc_by_pubid, stream_doc_file
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


@api.route('/<public_id>/file/')
@api.param('public_id', 'Doc public identifier')
class DocFile(Resource):
    @api.doc('Gets a File for a given Doc')
    @portal_token_required
    def get(self, public_id):
        doc = get_doc_by_pubid(public_id)
        if not doc:
            api.abort(404, message='That Doc could not be found.', success=False)

        try:
            return stream_doc_file(doc)

        except BadRequestError as e:
            api.abort(400, message='Error getting File for Doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error getting File for Doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to get File for Doc with ID {public_id}', success=False)
