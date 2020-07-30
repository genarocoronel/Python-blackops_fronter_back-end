from flask import Flask, request
from flask_restplus import Resource, Api

from app.main.util.decorator import token_required
from ..util.dto import DebtPaymentDto
from ..service.debt_payment_service import fetch_debt_payment_stats
from app.main.util.decorator import token_required

api = DebtPaymentDto.api 
_eft_return_fee = DebtPaymentDto.eft_return_fee

@api.route('/client/stats')
class DebtPaymentStats(Resource):
    @api.doc('Debt payment statuses for a given client')
    @token_required
    def get(self):
        try:
            client_id = request.args.get('client')
            start     = request.args.get('start', None)
            end       = request.args.get('end', None)
            data = fetch_debt_payment_stats(client_id, start, end)
            return data

        except Exception as err:
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400

@api.route('/eft-fee')
class EftReturnFeeView(Resource):
    @api.doc('create eft return fee')
    @token_required
    @api.marshal_with(_eft_return_fee)
    def post(self):
        try:
            data = request.json
            svc = EftFeeService()
            return svc.create(data)
        except Exception as e:
            api.abort(500, message=str(e), success=False)

    @api.doc('fetches eft return fee')
    @token_required
    @api.marshal_list_with(_eft_return_fee)
    def get(self):
        try:
            svc = EftFeeService()
            return svc.get()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

    
