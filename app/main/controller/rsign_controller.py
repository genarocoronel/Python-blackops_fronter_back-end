from flask import Flask, request
from flask_restplus import Resource, Api

from ..util.dto import RemoteSignDto
from ..model.docsign import DocusignSession, DocusignTemplate
from ..service.rsign_service import create_session, fetch_session_status

api = RemoteSignDto.api 
_ds_template = RemoteSignDto.docusign_template

@api.route('/docusign/templates')
class DsTemplateList(Resource):
    @api.doc('Docusign template list')
    @api.marshal_list_with(_ds_template, envelope='data')
    def get(self):
        """ List all available docusign templates """
        return DocusignTemplate.query.all() 

@api.route('/session/new')
class DsContractNew(Resource):
    @api.doc('Start a new session for remote signature')
    def post(self):
        try:
            data = request.json
            key = create_session(data)
            return { 'key' : key }

        except Exception as err:
            return {'message': 'Internal Server error'}, 400
   
@api.route('/session/<string:key>')
class DsContractStatus(Resource):
    @api.doc("fetch contract status")
    def get(self, key):
        return fetch_session_status(key)
