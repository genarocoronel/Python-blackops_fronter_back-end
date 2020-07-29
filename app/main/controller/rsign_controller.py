from flask import Flask, request
from flask_restplus import Resource, Api

from app.main.util.decorator import token_required
from ..util.dto import RemoteSignDto
from ..model.docsign import DocusignSession, DocusignTemplate
from ..service.rsign_service import create_session, fetch_session_status, fetch_client_status

api = RemoteSignDto.api 
_ds_template = RemoteSignDto.docusign_template

@api.route('/docusign/templates')
class DsTemplateList(Resource):
    @api.doc('Docusign template list')
    @api.marshal_list_with(_ds_template, envelope='data')
    @token_required
    def get(self):
        """ List all available docusign templates """
        return DocusignTemplate.query.all() 

@api.route('/session/new')
class DsContractNew(Resource):
    @api.doc('Start a new session for remote signature')
    @token_required
    def post(self):
        try:
            data = request.json
            key = create_session(data)
            return { 'key' : key }

        except Exception as err:
            print(str(err))
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400
   
@api.route('/session/<string:key>')
class DsContractStatus(Resource):
    @api.doc("fetch contract status")
    @token_required
    def get(self, key):
        try:
            return fetch_session_status(key)
        except Exception as err:
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400

@api.route('/client/<string:client_id>/status')
class DsClientStatus(Resource):
    @api.doc("fetch client docusign status")
    @token_required
    def get(self, client_id):
        try:
            return fetch_client_status(client_id)

        except Exception as err:
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400
