from flask import request
from flask import g
from flask_restplus import Resource


from app.main.core.auditor import Auditor
from app.main.util.decorator import token_required, user_has_permission

from app.main.util.dto import AuditDto
from flask import current_app as app

from app.main.tasks.audit import record

api = AuditDto.api
_audit = AuditDto.audit


@api.route('/')
class Audit(Resource):
    @api.doc('Create Audit item')
    @api.marshal_with(_audit)
    @token_required
    def post(self):
        """ Create Audit item """
        request_data = request.json
        curr_user = g.current_user
        
        try:
            Auditor.launch_task(
                auditable=request_data['auditable'],
                auditable_subject_pubid=request_data['auditable_subject_id'],
                action=request_data['action'],
                requestor_username=curr_user['username'],
                message=request_data['message'],
                is_internal=False
                )

        except Exception as e:
            api.abort(500, message=str(e), success=False)

        return {'success': True, 'message': 'Audit recording request received'}, 200