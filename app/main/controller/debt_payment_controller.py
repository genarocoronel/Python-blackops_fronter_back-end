from flask import Flask, request
from flask_restplus import Resource, Api

from ..util.dto import DebtPaymentDto
from ..service.debt_payment_service import create_debt_payment_account, fetch_debt_payment_stats

api = DebtPaymentDto.api 

@api.route('/client/add')
class DebtPaymentAdd(Resource):
    @api.doc('Add a client to the debt payment schedule')
    def post(self):
        try:
            data = request.json
            client_id = data['client_id']
            create_debt_payment_account(client_id)
            return { 'message':'Success' }

        except Exception as err:
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400
   

@api.route('/client/stats')
class DebtPaymentStats(Resource):
    @api.doc('Debt payment statuses for a given client')
    def get(self):
        try:
            client_id = request.args.get('client')
            start     = request.args.get('start', None)
            end       = request.args.get('end', None)
            data = fetch_debt_payment_stats(client_id, start, end)
            return data

        except Exception as err:
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400
