from flask import request
from flask_restplus import Resource

from app.main.controller import _convert_payload_datetime_values, _handle_get_client, _handle_get_credit_report
from app.main.model.client import ClientType
from app.main.service.debt_service import check_existing_scrape_task, get_report_data
from app.main.service.client_service import get_all_clients, save_new_client, get_client, get_client_appointments, \
    update_client, get_client_employments, get_all_clients_dispositions, update_client_employments, get_client_income_sources, update_client_income_sources, \
    get_client_monthly_expenses, update_client_monthly_expenses, save_changes, update_client_addresses, \
    get_client_addresses
from ..util.dto import ClientDto, AppointmentDto

api = ClientDto.api
_client = ClientDto.client
_update_client = ClientDto.update_client
_client_employment = ClientDto.client_employment
_client_dispositions = ClientDto.client_dispositions
_update_client_employment = ClientDto.update_client_employment
_appointment = AppointmentDto.appointment
_client_income = ClientDto.client_income
_update_client_income = ClientDto.update_client_income
_client_monthly_expense = ClientDto.client_monthly_expense
_update_client_monthly_expense = ClientDto.update_client_monthly_expense
_credit_report_debt = ClientDto.credit_report_debt
_update_client_address = ClientDto.update_client_address
_client_address = ClientDto.client_address

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

@api.route('/dispositions')
class ClientDispositionsList(Resource):
    @api.doc('list_of_client_dispositions')
    @api.marshal_list_with(_client_dispositions, envelope='data')
    def get(self):
        """ List all client dispositions"""
        client_disposiitions = get_all_clients_dispositions()
        return client_disposiitions

@api.route('/<public_id>')
@api.param('public_id', 'The Client Identifier')
@api.response(404, 'Client not found')
class Client(Resource):
    @api.doc('get client')
    @api.marshal_with(_client)
    def get(self, public_id):
        """ Get client with provided identifier"""
        client, error_response = _handle_get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            return client

    @api.doc('update client')
    @api.expect(_update_client, validate=True)
    def put(self, public_id):
        """ Update client with provided identifier"""
        client = get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404)
        else:
            return update_client(client, request.json, client_type=CLIENT)


@api.route('/<client_id>/income-sources')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientIncomeSources(Resource):
    @api.doc('get client income sources')
    @api.marshal_list_with(_client_income)
    def get(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_income_sources(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update client income sources')
    @api.expect([_update_client_income], validate=True)
    def put(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            numbers = request.json
            result, err_msg = update_client_income_sources(client, numbers)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<client_id>/monthly-expenses')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientMonthlyExpenses(Resource):
    @api.doc('get client monthly expenses')
    @api.marshal_list_with(_client_monthly_expense)
    def get(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_monthly_expenses(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update client monthly expenses')
    @api.expect([_update_client_monthly_expense], validate=True)
    def put(self, client_id):
        client, error_response = _handle_get_client(client_id)
        if not client:
            api.abort(404, **error_response)
        else:
            expenses = request.json
            result, err_msg = update_client_monthly_expenses(client, expenses)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


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
        client, error_response = _handle_get_client(public_id, client_type=CLIENT)
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
        client, error_response = _handle_get_client(public_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            employments = request.json
            _convert_payload_datetime_values(employments, 'start_date', 'end_date')

            result, err_msg = update_client_employments(client, employments)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<client_id>/addresses')
@api.param('client_id', 'Client public identifier')
@api.response(404, 'Client not found')
class ClientAddresses(Resource):
    @api.response(200, 'Address successfully created')
    @api.doc('create new address')
    @api.expect([_update_client_address], validate=True)
    def put(self, client_id):
        """ Creates new Address """
        print(client_id)
        addresses = request.json
        client, error_response = _handle_get_client(client_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        return update_client_addresses(client, addresses)

    @api.doc('get client addresses')
    @api.marshal_list_with(_client_address)
    def get(self, client_id):
        client, error_response = _handle_get_client(client_id, client_type=CLIENT)
        if not client:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_client_addresses(client)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200


@api.route('/<public_id>/credit-report/debts')
@api.param('public_id', 'The client Identifier')
@api.response(404, 'client or credit report account does not exist')
class ClientCreditReportDebts(Resource):
    @api.doc('fetch credit report data')
    def put(self, public_id):
        """ Fetch Credit Report Data"""
        client, error_response = _handle_get_client(public_id, ClientType.lead)
        if not client:
            api.abort(404, **error_response)

        credit_account, error_response = _handle_get_credit_report(client)
        if not credit_account:
            api.abort(404, **error_response)

        exists, error_response = check_existing_scrape_task(credit_account)
        if exists:
            api.aport(409, **error_response)

        task = credit_account.launch_spider(
            'capture',
            'Capture credit report debts for lead',  # TODO: allow passing custom message for task execution
        )
        save_changes(task)

        resp = {
            'message': 'Spider queued',
            'task_id': task.id
        }
        return resp, 200

    @api.doc('view credit report data')
    @api.marshal_list_with(_credit_report_debt, envelope='data')
    def get(self, public_id):
        """ View Credit Report Data """
        lead, error_response = _handle_get_client(public_id, ClientType.lead)
        if not lead:
            api.abort(404, **error_response)

        credit_account, error_response = _handle_get_credit_report(lead)
        if not credit_account:
            api.abort(404, **error_response)

        data = get_report_data(credit_account)
        return data, 200