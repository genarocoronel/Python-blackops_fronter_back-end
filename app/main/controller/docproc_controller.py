from flask import request
from flask_restplus import Resource

from app.main.util.dto import DocprocDto
from app.main.util.decorator import (token_required, enforce_rac_policy, enforce_rac_required_roles)
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.core.rac import RACRoles
from app.main.service.docproc_service import (get_all_docs, get_doc_by_pubid, assign_for_processing, 
    update_doc, move_to_client_dossier, create_doc_note, allowed_doc_file_kinds, attach_file_to_doc,
    create_doc_manual, stream_doc_file)
from app.main.service.user_service import get_a_user
from app.main.service.client_service import get_client_by_public_id
from flask import current_app as app

api = DocprocDto.api
_doc = DocprocDto.doc
_doc_create = DocprocDto.doc_create
_doc_assignment = DocprocDto.doc_assignment
_doc_update = DocprocDto.doc_update
_doc_move = DocprocDto.doc_move
_doc_note_create = DocprocDto.doc_note_create
_doc_upload = DocprocDto.doc_upload

@api.route('')
class Doc(Resource):
    @api.doc('Creates a Doc')
    @api.expect(_doc_create, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def post(self):
        """ Creates a Doc manually """
        request_data = request.json

        try:
            doc = create_doc_manual(request_data)

        except BadRequestError as e:
            api.abort(400, message='Error creating doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error creating doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to create Doc', success=False)

        return doc, 200
    
    @api.doc('Gets a list of Docs')
    @api.marshal_list_with(_doc, envelope='data')
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def get(self):
        """ Gets a list of Docs """
        return get_all_docs()


@api.route('/<doc_public_id>/assign/')
@api.param('doc_public_id', 'Doc public ID')
class DocAssign(Resource):    
    @api.doc('Assigns a Doc to a Doc Processor user')
    @api.expect(_doc_assignment, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR])
    def put(self, doc_public_id):
        """ Assigns a Doc to a Doc Processor user """
        request_data = request.json

        doc = get_doc_by_pubid(doc_public_id)
        if not doc:
            api.abort(404, message='That Doc could not be found.', success=False)

        docproc_user = get_a_user(request_data['public_id'])
        if not docproc_user:
            api.abort(404, message='That Doc Processor Rep could not be found.', success=False)
        
        try:
            updated_doc = assign_for_processing(doc, docproc_user)

        except BadRequestError as e:
            api.abort(400, message='Error assigning Doc to Doc Processor, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error assigning Doc to Doc Processor, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to assigning Doc with ID {doc_public_id} to Doc Processor with ID {request_data["public_id"]}', success=False)
        
        return updated_doc, 200


@api.route('/<doc_public_id>/')
@api.param('doc_public_id', 'Doc public ID')
class Docproc(Resource):
    @api.doc('Updates a Doc')
    @api.expect(_doc_update, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def put(self, doc_public_id):
        """ Updates a Doc """
        request_data = request.json
        doc = get_doc_by_pubid(doc_public_id)
        if not doc:
            api.abort(404, message='That Doc could not be found.', success=False)

        try:
            updated_doc = update_doc(doc, request_data)

        except BadRequestError as e:
            api.abort(400, message='Error updating doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error updating doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to update Doc with ID {doc_public_id}', success=False)

        return updated_doc, 200


@api.route('/<doc_public_id>/move/')
@api.param('doc_public_id', 'Doc public ID')
class DocMove(Resource):
    @api.doc('Moves a Doc to a Client "Dossier/File"')
    @api.expect(_doc_move, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def put(self, doc_public_id):
        """ Moves a Doc to a Client "Dossier/File" """
        request_data = request.json

        doc = get_doc_by_pubid(doc_public_id)
        if not doc:
            api.abort(404, message='That Doc could not be found.', success=False)

        client = get_client_by_public_id(request_data['public_id'])
        if not client:
            api.abort(404, message='That Client could not be found.', success=False)
        
        try:
            updated_doc = move_to_client_dossier(doc, client)

        except BadRequestError as e:
            api.abort(400, message='Error moving Doc to Client dossier, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error moving Doc to Client dossier, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to move Doc with ID {doc_public_id} to Client with ID {request_data["public_id"]}', success=False)
        
        return updated_doc, 200


@api.route('/<doc_public_id>/note/')
@api.param('doc_public_id', 'Doc public ID')
class DocNote(Resource):
    @api.doc('Creates a Doc Note')
    @api.expect(_doc_note_create, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def post(self, doc_public_id):
        """ Creates a Doc Note """
        request_data = request.json

        doc = get_doc_by_pubid(doc_public_id)
        if not doc:
            api.abort(404, message='That Doc could not be found.', success=False)
        
        try:
            updated_doc = create_doc_note(doc, request_data['content'])

        except BadRequestError as e:
            api.abort(400, message='Error creating a Note for Doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error creating a Note for Doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to create Note for Doc with ID {doc_public_id}', success=False)
        
        return updated_doc, 200


@api.route('/<doc_public_id>/upload/')
@api.param('doc_public_id', 'Doc public ID')
class DocUpload(Resource):
    @api.doc('Uploads a File to a Doc')
    @api.expect(_doc_upload, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
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


@api.route('/<doc_public_id>/file/')
@api.param('doc_public_id', 'Doc public ID')
class DocFile(Resource):
    @api.doc('Gets a Doc File')
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
    def get(self, doc_public_id):
        """ Gets a Doc File stream """

        doc = get_doc_by_pubid(doc_public_id)
        if not doc:
            api.abort(404, message='That Doc could not be found.', success=False)
        
        try:
            return stream_doc_file(doc)

        except BadRequestError as e:
            api.abort(400, message='Error getting File for Doc, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error getting File for Doc, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to get File for Doc with ID {doc_public_id}', success=False)
