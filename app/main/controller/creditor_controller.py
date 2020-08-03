from flask import request
from flask_restplus import Resource

from app.main.model.creditor import Creditor
from app.main.service.creditor import CreditorService
from app.main.util.dto import CreditorDto
from app.main.util.decorator import token_required

api = CreditorDto.api
_creditor = CreditorDto.creditor

@api.route('/')
class CreditorList(Resource):
    @api.marshal_with(_creditor)
    @token_required
    def post(self): 
        """ Create Creditor """
        try:
            payload = request.json
            svc = CreditorService()
            return svc.create(payload)
        except Exception as e:
            api.abort(500, message=str(e), success=False)

    @api.doc('list all creditors')
    @api.marshal_list_with(_creditor)
    @token_required
    def get(self):
        """ List all creditors """
        try:
            cs = CreditorService()
            creditors = cs.get()
            return creditors, 200
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/<creditor_id>')
@api.param('creditor_id', 'Creditor Identifier')
class CreditorItem(Resource):
    @api.marshal_with(_creditor)
    @token_required
    def put(self, creditor_id):
        """ Update Creditor Information """
        payload = request.json
        try:
            service = CreditorService()
            return service.update(creditor_id, payload)

        except Exception as e:
            api.abort(500, message=str(e), success=False)
