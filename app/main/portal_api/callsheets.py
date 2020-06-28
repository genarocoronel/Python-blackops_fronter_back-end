from flask import request
from flask_restplus import Resource

from app.main.util.portal_dto import CallsheetDto
from app.main.util.decorator import portal_token_required
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.service.portal_callsheet_service import (get_callsheets_for_portal_user, create_callsheet,
    get_callsheet_by_pubid, attach_file_to_callsheet, stream_callsheet_file)
from app.main.service.docproc_service import allowed_doc_file_kinds
from flask import current_app as app


api = CallsheetDto.api
_callsheet = CallsheetDto.callsheet
_callsheet_create = CallsheetDto.callsheet_create
_callsheet_upload = CallsheetDto.callsheet_upload

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


@api.route('/<callsheet_pub_id>/upload/')
@api.param('callsheet_pub_id', 'Callsheet public ID')
class CallsheetUpload(Resource):
    @api.doc('Uploads a File to a Callsheet')
    @api.expect(_callsheet_upload, validate=True)
    @portal_token_required
    def post(self, callsheet_pub_id):
        """ Uploads a File to a Callsheet """

        callsheet = get_callsheet_by_pubid(callsheet_pub_id)
        if not callsheet:
            api.abort(404, message='That Callsheet could not be found.', success=False)

        args = _callsheet_upload.parse_args()
        file = args['doc_file']
        
        if not file:
            api.abort(400, message='Callsheet file is missing from the request.', success=False)
        elif file.filename == '':
            api.abort(400, message='No Callsheet file was selected.', success=False)

        if not allowed_doc_file_kinds(file.filename):
            api.abort(400, message='That Callsheet file kind is not allowed. Try PDF, PNG, JPG, JPEG, or GIF.', success=False)
        
        try:
            updated_callsheet = attach_file_to_callsheet(callsheet, file)

        except BadRequestError as e:
            api.abort(400, message='Error uploading file for Callsheet, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error uploading file for Callsheet, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to upload File for Callsheet with ID {callsheet_pub_id}', success=False)
        
        return updated_callsheet, 200


@api.route('/<public_id>/file/')
@api.param('public_id', 'Callsheet public identifier')
class CallsheetFile(Resource):
    @api.doc('Gets a File for a given Callsheet')
    @portal_token_required
    def get(self, public_id):
        callsheet = get_callsheet_by_pubid(public_id)
        if not callsheet:
            api.abort(404, message='That Callsheet could not be found.', success=False)

        if not callsheet.docproc:
            api.abort(400, message='That Callsheet does not have a file attached.', success=False)
            
        try:
            return stream_callsheet_file(callsheet.docproc)

        except BadRequestError as e:
            api.abort(400, message='Error getting File for Callsheet, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error getting File for Callsheet, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to get File for Callsheet with ID {public_id}', success=False)