from flask import request
from flask_restplus import Resource

from app.main.model.client import ClientType
from app.main.service.client_service import get_all_clients, save_new_client, get_client, get_client_appointments, get_client_employments, update_client_employments
from ..util.dto import ClientDto, AppointmentDto

api = ClientDto.api
_client = ClientDto.client
_client_employment = ClientDto.client_employment
_update_client_employment = ClientDto.update_client_employment
_appointment = AppointmentDto.appointment

CLIENT = ClientType.client


@api.route('/')
class ClientList(Resource):
    @api.doc('list_of_clients')
    @api.marshal_list_with(_client, envelope='data')
    def get(self):
        """ List all clients """
        clients = get_all_clients(client_type=CLIENT)
        return clients

    @api.response(201, 'Client successfully created')
    @api.doc('create new client')
    @api.expect(_client, validate=True)
    def post(self):
        """ Creates new Client """
        data = request.json
        return save_new_client(data=data, client_type=CLIENT)


@api.route('/<public_id>')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Client not found')
class Client(Resource):
    @api.doc('get client')
    @api.marshal_with(_client)
    def get(self, public_id):
        """ Get client with provided identifier"""
        client = get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404)
        else:
            return client


@api.route('/<public_id>/appointments')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Client not found')
class ClientAppointmentList(Resource):
    @api.doc('get client')
    @api.marshal_with(_appointment)
    def get(self, public_id):
        """ Get client appointments """
        result = get_client_appointments(public_id, client_type=CLIENT)
        if result is None:
            api.abort(404)
        else:
            return result


@api.route('/<public_id>/employments')
@api.param('public_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientEmployments(Resource):
    @api.doc('get client employments')
    @api.marshal_list_with(_client_employment)
    def get(self, public_id):
        client, error_response = get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_employments(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update client employment')
    @api.expect([_update_client_employment], validate=True)
    def put(self, public_id):
        client, error_response = get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            employments = request.json
            result, err_msg = update_client_employments(client, employments)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200
