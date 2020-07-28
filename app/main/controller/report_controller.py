from flask import Flask, request
from flask_restplus import Resource
from app.main.util.dto import ReportDto
from app.main.util.decorator import token_required

from app.main.service.report import ClientReportSvc, SalesReportSvc, ACHReportSvc, FutureDraftReportSvc,\
                                    CollectorReportSvc, CreditorReportSvc, TaskReportSvc

api = ReportDto.api

@api.route('/clients_report/view')
class ClientReportView(Resource):
    @api.doc('Fetches all leads & clients report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = ClientReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/clients_report')
class ClientReportDownload(Resource):
    @api.doc('Download All leads & clients report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = ClientReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/sales_report/view')
class SalesReportView(Resource):
    @api.doc('Fetches Sales report')
    @token_required
    def get(self):
        try:
            data = request.json 
            svc = SalesReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/sales_report')
class SalesReportDownload(Resource):
    @api.doc('Download Sales report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = SalesReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/ach_report/view')
class ACHReportView(Resource):
    @api.doc('Fetches ACH report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = ACHReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/ach_report')
class ACHReportDownload(Resource):
    @api.doc('Download ACH report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = ACHReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/future_draft_report/view')
class FutureDraftReportView(Resource):
    @api.doc('Fetches future-draft report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = FutureDraftReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/future_draft_report')
class FutureDraftReportDownload(Resource):
    @api.doc('Fetches future-draft report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = FutureDraftReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/debt_collector_report/view')
class DebtCollectorReportView(Resource):
    @api.doc('Fetches Debt Collector report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = CollectorReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/debt_collector_report')
class DebtCollectorReportDownload(Resource):
    @api.doc('Fetches Debt Collector report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = CollectorReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/creditor_report/view')
class CreditorReportView(Resource):
    @api.doc('Fetches Creditor report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = CreditorReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/creditor_report')
class CreditorReportDownload(Resource):
    @api.doc('Fetches Creditor report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = CreditorReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/task_report/view')
class TaskReportView(Resource):
    @api.doc('Fetches Task report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = TaskReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/task_report')
class TaskReportDownload(Resource):
    @api.doc('Fetches Task report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = TaskReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)
