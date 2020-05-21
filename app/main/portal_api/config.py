from flask_restplus import Resource

from app.main.util.portal_dto import ConfigDto
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.service.config_service import get_all_docproc_types
from flask import current_app as app


api = ConfigDto.api
_docproc_types = ConfigDto.docproc_types

@api.route('/doc-types')
class DocprocTypes(Resource):
    @api.doc('Get known Doc Types')
    @api.marshal_list_with(_docproc_types, envelope='data')
    def get(self):
        """ Get all Doc Types """
        try:
            types = get_all_docproc_types()
        except NotFoundError as e:
            api.abort(404, message='Error getting Doc types, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed get Doc types. Please report this issue.', success=False)    
        
        return types, 200