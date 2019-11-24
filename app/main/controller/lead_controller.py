from flask import request
from flask_restplus import Resource

from app.main.model.client import ClientType
from app.main.service.client_service import get_all_clients, save_new_client, get_client
from ..util.dto import LeadDto

api = LeadDto.api
_lead = LeadDto.lead

LEAD = ClientType.lead


@api.route('/')
class LeadList(Resource):
    @api.doc('list_of_clients')
    @api.marshal_list_with(_lead, envelope='data')
    def get(self):
        """ List all clients """
        clients = get_all_clients(client_type=LEAD)
        return clients

    @api.response(201, 'Client successfully created')
    @api.doc('create new client')
    @api.expect(_lead, validate=True)
    def post(self):
        """ Creates new Client """
        data = request.json
        return save_new_client(data=data, client_type=LEAD)


@api.route('/<public_id>')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Client not found')
class Lead(Resource):
    @api.doc('get client')
    @api.marshal_with(_lead)
    def get(self, public_id):
        """ Get client with provided identifier"""
        client = get_client(public_id, client_type=LEAD)
        if not client:
            api.abort(404)
        else:
            return client



