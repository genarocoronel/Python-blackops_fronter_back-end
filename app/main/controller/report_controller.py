from flask import Flask, request
from flask_restplus import Resource
from app.main.util.dto import ReportDto
from app.main.util.decorator import token_required
from app.main.service.report import ClientReportSvc, SalesReportSvc, ACHReportSvc, FutureDraftReportSvc,\
                                    CollectorReportSvc, CreditorReportSvc, TaskReportSvc, DaysDelinquentReportSvc,\
                                    StaffReportSvc, TeamReportSvc, PostMailReportSvc, DebtMgmtReportSvc,\
                                    EftReturnFeeReportSvc, NotificationReportSvc, StatusReportSvc

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

@api.route('/days_delinquent_report/view')
class DeysDelinquentReportView(Resource):
    @api.doc('Fetches Days Delinquent report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = DaysDelinquentReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/days_delinquent_report')
class DaysDelinquentReportDownload(Resource):
    @api.doc('Downloads days delinquent report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = DaysDelinquentReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/eft_return_fee_report/view')
class EftReturnFeeReportView(Resource):
    @api.doc('Fetches EFT Return fee report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = EftReturnFeeReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)


@api.route('/eft_return_fee_report')
class EftReturnFeeReportDownload(Resource):
    @api.doc('Download EFT Return fee report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = EftReturnFeeReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/post_mail_print_report/view')
class PostMailPrintReportView(Resource):
    @api.doc('Fetches Post Mail Print report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = PostMailReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/post_mail_print_report')
class PostMailPrintReportDownload(Resource):
    @api.doc('Download Post mail print report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = PostMailReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/team_report/view')
class TeamReportView(Resource):
    @api.doc('Fetches team report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = TeamReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/team_report')
class TeamReportDownload(Resource):
    @api.doc('Download team report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = TeamReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/staff_report/view')
class StaffReportView(Resource):
    @api.doc('Fetches staff management report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = StaffReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/staff_report')
class StaffReportDownload(Resource):
    @api.doc('Download staff management report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = StaffReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/debt_mgmt_report/view')
class DebtMgmtReportView(Resource):
    @api.doc('Fetches Debt management report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = DebtMgmtReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/debt_mgmt_report')
class DebtMgmtReportDownload(Resource):
    @api.doc('Downloads Debt management report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = DebtMgmtReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/notification_report/view')
class NotificationReportView(Resource):
    @api.doc('Fetches Notification report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = NotificationReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/notification_report')
class NotificationReportDownload(Resource):
    @api.doc('Downloads Notification report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = NotificationReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/status_report/view')
class StatusReportView(Resource):
    @api.doc('Fetches Status report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = StatusReportSvc()
            return svc.view()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/status_report')
class StatusReportDownload(Resource):
    @api.doc('Downloads Status report')
    @token_required
    def get(self):
        try:
            data = request.json
            svc = StatusReportSvc()
            return svc.download()
        except Exception as e:
            api.abort(500, message=str(e), success=False)

