from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import DocDto
from app.main.util.decorator import portal_token_required
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.model.docproc import DocprocChannel
from app.main.service.docproc_service import (get_docs_for_portal_user, get_doc_by_pubid, stream_doc_file,
    create_doc_manual, get_doc_by_pubid, allowed_doc_file_kinds, attach_file_to_doc)
from flask import current_app as app

api = DocDto.api
_doc = DocDto.doc
_doc_create = DocDto.doc_create
_doc_upload = DocDto.doc_upload

@api.route('')
class Doc(Resource):
    @api.doc('Gets a list of Docs')
    @api.marshal_list_with(_doc, envelope='data')
    @portal_token_required
    def get(self):
        """ Gets a list of Docs """
        docs = get_docs_for_portal_user()

        return docs, 200

    @api.doc('Creates a Doc')
    @api.expect(_doc_create, validate=True)
    @portal_token_required
    def post(self):
        """ Creates a Doc manually """
        request_data = request.json
        request_data['source_channel'] = DocprocChannel.PORTAL.value

        try:
            doc = create_doc_manual(request_data)

        except BadRequestError as e:
            api.abort(400, message='Error creating doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error creating doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to create Doc', success=False)

        return doc, 200


@api.route('/<doc_public_id>/upload/')
@api.param('doc_public_id', 'Doc public ID')
class DocUpload(Resource):
    @api.doc('Uploads a File to a Doc')
    @api.expect(_doc_upload, validate=True)
    @portal_token_required
    def post(self, doc_public_id):
        """ Uploads a File to a Doc """

        doc = get_doc_by_pubid(doc_public_id)
        if not doc:
            api.abort(404, message='That Doc could not be found.', success=False)

        args = _doc_upload.parse_args()
        file = args['doc_file']
        
        if not file:
            api.abort(400, message='Doc file is missing from the request.', success=False)
        elif file.filename == '':
            api.abort(400, message='No Doc file was selected.', success=False)

        if not allowed_doc_file_kinds(file.filename):
            api.abort(400, message='That Doc file kind is not allowed. Try PDF, PNG, JPG, JPEG, or GIF.', success=False)
        
        try:
            updated_doc = attach_file_to_doc(doc, file)

        except BadRequestError as e:
            api.abort(400, message='Error uploading file for Doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error uploading file for Doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to upload File for Doc with ID {doc_public_id}', success=False)
        
        return updated_doc, 200


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