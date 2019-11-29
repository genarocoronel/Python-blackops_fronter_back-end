import os
import uuid
import traceback
from flask import request, current_app
from flask_restplus import Resource
from werkzeug.utils import secure_filename
from app.main import db
from app.main.config import upload_location
from app.main.model.client import ClientType
from app.main.model.task import ScrapeTask
from app.main.model.candidate import Candidate
from app.main.model.credit_report_account import CreditReportSignupStatus,\
    CreditReportData, CreditReportAccount
from app.main.service.candidate_service import save_new_candidate_import,\
    get_all_candidates, update_candidate, save_changes

from app.main.service.credit_report_account_service import\
    save_new_credit_report_account, update_credit_report_account

from app.main.service.debt_service import get_report_data, check_existing_scrape_task

from app.main.service.client_service import get_all_clients, save_new_client, get_client

from ..util.dto import CandidateDto, TestAPIDto, LeadDto

api = TestAPIDto.api
_candidate_upload = CandidateDto.candidate_upload
_import = CandidateDto.imports
_new_credit_report_account = CandidateDto.new_credit_report_account
_update_credit_report_account = CandidateDto.update_credit_report_account
_candidate = CandidateDto.candidate
_lead = LeadDto.lead
_credit_report_data = CandidateDto.credit_report_data
_update_candidate = CandidateDto.update_candidate


@api.route('/candidates')
class GetCandidates(Resource):
    @api.doc('get all candidates')
    @api.marshal_list_with(_candidate, envelope='data')
    def get(self):
        """Get all Candidates"""
        candidates = get_all_candidates()
        return candidates, 200


@api.route('/candidates/delete_all')
class DeleteCandidates(Resource):
    @api.doc('delete all candidates')
    def put(self):
        """ Delete all Candidates """
        candidates = get_all_candidates()
        for c in candidates:
            db.session.delete(c)
            db.session.commit()
        response_object = {
            'success': True,
            'message': 'Candidates Deleted'
        }
        return response_object, 200


@api.route('/candidates/<candidate_id>')
@api.response(404, 'Candidate not found')
class UpdateCandidate(Resource):
    @api.doc('get candidate')
    @api.marshal_with(_candidate)
    def get(self, candidate_id):
        """Get candidate"""
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        return candidate, 200

    @api.doc('update candidate')
    @api.expect(_update_candidate, validate=True)
    def put(self, public_id):
        """Update candidate"""
        return update_candidate(public_id, request.json)


@api.route('/candidates/upload')
class CandidateUpload(Resource):
    @api.doc('create candidates from file')
    @api.expect(_candidate_upload, validate=True)
    def post(self):
        """Upload candidate csv"""

        args = _candidate_upload.parse_args()
        file = args['csv_file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_location, filename)
            file.save(file_path)

            candidate_import = save_new_candidate_import(
                {'file_path': file_path})
            task = candidate_import.launch_task(
                'parse_candidate_file',
                'Parse uploaded candidate file and load db with entries'
            )

            save_changes()

            resp = {'task_id': task.id}
            return resp, 200

        else:
            return {'status': 'failed', 'message': 'No file was provided'}, 409


def _handle_get_candidate(public_id):
    print('public_id:', public_id)
    candidate = Candidate.query.filter_by(public_id=public_id).first()
    if not candidate:
        response_object = {
            'success': False,
            'message': 'Candidate does not exist'
        }
        return None, response_object
    else:
        return candidate, None


def _handle_get_credit_report(candidate, account_public_id):
    account = candidate.credit_report_account
    return account, None


def save_new_account_for_lead(data, lead, status: CreditReportSignupStatus = None):
    account = CreditReportAccount.query.filter_by(
        customer_token=data.get('customer_token'),
        tracking_token=data.get('tracking_token')).first()
    if not account:
        new_account = CreditReportAccount(
            public_id=str(uuid.uuid4()),
            customer_token=data.get('customer_token'),
            provider=data.get('provider'),
            tracking_token=data.get('tracking_token') or data.get('trackingToken'),
            plan_type=data.get('plan_type'),
            financial_obligation_met=data.get('financial_obligation_met'),
            status=status or CreditReportSignupStatus.INITIATING_SIGNUP,
            client=lead,
            email=data.get('email'),
        )
        save_changes(new_account)
        return new_account
    else:
        raise Exception('Credit Report Account already exists')


@api.route('/candidates/<candidate_public_id>/credit-report/account')
@api.param('candidate_public_id', 'The Candidate Identifier')
class CreateCreditReportAccount(Resource):
    @api.doc('create credit report account')
    @api.expect(_new_credit_report_account, validate=True)
    def post(self, candidate_public_id):
        """Create Credit Report Account for Candidate"""
        request_data = request.json

        try:
            candidate, error_response = _handle_get_candidate(
                candidate_public_id)
            if not candidate:
                api.abort(404, **error_response)

            # look for existing credit report account
            credit_report_account = candidate.credit_report_account
            if not credit_report_account:
                signup_data = {
                    'customer_token': 'my_customer_token',
                    'tracking_token': 'my_tracking_token',
                    'provider': 'Smart Credit',
                    'plan_type': 'my_plan_type',
                    'financial_obligation_met': True,
                    'email': request_data.get('email'),
                }
                credit_report_account = save_new_credit_report_account(
                    signup_data,
                    candidate,
                    CreditReportSignupStatus.INITIATING_SIGNUP
                )

            if credit_report_account.status ==\
               CreditReportSignupStatus.ACCOUNT_CREATED:
                response_object = {
                    'success': False,
                    'message': 'Credit Report account already exists'
                }
                return response_object, 409

            credit_report_account.password = '12345678'
            credit_report_account.customer_token = 'mycustomerToken'
            credit_report_account.financial_obligation_met = True
            credit_report_account.plan_type = 'myPlan'
            credit_report_account.status =\
                CreditReportSignupStatus.ACCOUNT_CREATED
            update_credit_report_account(credit_report_account)

            response_object = {
                'success': True,
                'message': 'Successfully created credit report '
                           f'account with {credit_report_account.provider}',
                'public_id': credit_report_account.public_id
            }
            return response_object, 201

        except Exception as e:
            traceback.print_exc()
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/candidates/<public_id>/credit-report/debts')
@api.param('public_id', 'The Candidate Identifier')
class CreditReportDebts(Resource):
    @api.doc('fetch credit report data')
    def put(self, public_id):
        """ Fetch Credit Report Data for Candidate"""
        try:
            candidate, error_response = _handle_get_candidate(public_id)
            if not candidate:
                api.abort(404, **error_response)
            account, error_response = _handle_get_credit_report(
                candidate, public_id)
            if not account:
                return error_response
            exists, error_response = check_existing_scrape_task(account)
            if exists:
                return error_response
            task = CreditReportData().launch_spider(
                account.id,
                account.email,
                current_app.cipher.decrypt(
                    account.password).decode()
            )

            save_changes()

            resp = {
                'messsage': 'Spider queued',
                'task_id': task.id
            }
            return resp, 200
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

    @api.doc('view credit report data')
    @api.marshal_list_with(_credit_report_data, envelope='data')
    def get(self, public_id):
        """View Credit Report Data for Candidate"""
        candidate, error_response = _handle_get_candidate(public_id)
        if not candidate:
            api.abort(404, **error_response)
        data = get_report_data(candidate.credit_report_account)
        return data, 200


@api.route('/leads')
class LeadList(Resource):
    @api.doc('list_of_leads')
    @api.marshal_list_with(_lead, envelope='data')
    def get(self):
        """List all Leads"""
        leads = get_all_clients(client_type=ClientType.lead)
        return leads

    @api.response(201, 'Lead successfully created')
    @api.doc('create new lead')
    @api.expect(_lead, validate=True)
    def post(self):
        """Creates new Lead"""
        data = request.json
        return save_new_client(data=data, client_type=ClientType.lead)


@api.route('/leads/delete_all')
class DeleteLeads(Resource):
    @api.doc('delete all leads')
    def put(self):
        """Delete all Leads"""
        leads = get_all_clients(client_type=ClientType.lead)
        for l in leads:
            db.session.delete(l)
            db.session.commit()
        response_object = {
            'success': True,
            'message': 'Leads Deleted'
        }
        return response_object, 200


@api.route('/leads/<public_id>')
@api.response(404, 'Lead not found')
class UpdateLead(Resource):
    @api.doc('get lead')
    @api.marshal_with(_lead)
    def get(self, public_id):
        """Get Lead"""
        lead = get_client(public_id, client_type=ClientType.lead)
        if not lead:
            error_response = {
                    'success': False,
                    'message': 'Lead not found'
                }
            api.abort(404, **error_response)
        return lead, 200


@api.route('/leads/<public_id>/credit-report/account')
@api.param('public_id', 'The Lead Identifier')
class CreateCreditReportAccountLead(Resource):
    @api.doc('create credit report account for lead')
    @api.expect(_new_credit_report_account, validate=True)
    def post(self, public_id):
        """Create Credit Report Account for Lead"""
        request_data = request.json

        try:
            lead = get_client(public_id, client_type=ClientType.lead)
            if not lead:
                error_response = {
                    'success': False,
                    'message': 'Lead not found'
                }
                api.abort(404, **error_response)

            # look for existing credit report account
            credit_report_account = lead.credit_report_account
            if not credit_report_account:
                signup_data = {
                    'customer_token': 'my_customer_token_LEAD',
                    'tracking_token': 'my_tracking_token_LEAD',
                    'provider': 'Smart Credit_LEAD',
                    'plan_type': 'my_plan_type_LEAD',
                    'financial_obligation_met': True,
                    'email': request_data.get('email'),
                }
                credit_report_account = save_new_account_for_lead(
                    signup_data,
                    lead,
                    CreditReportSignupStatus.INITIATING_SIGNUP
                )

            if credit_report_account.status ==\
               CreditReportSignupStatus.ACCOUNT_CREATED:
                response_object = {
                    'success': False,
                    'message': 'Credit Report account already exists'
                }
                return response_object, 409

            credit_report_account.password = '12345678'
            credit_report_account.status =\
                CreditReportSignupStatus.ACCOUNT_CREATED
            save_changes(credit_report_account)

            response_object = {
                'success': True,
                'message': 'Successfully created credit report '
                           f'account with {credit_report_account.provider}',
                'public_id': credit_report_account.public_id
            }
            return response_object, 201

        except Exception as e:
            traceback.print_exc()
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/leads/<public_id>/credit-report/debts')
@api.param('public_id', 'The Candidate Identifier')
class CreditReportDebtsLead(Resource):
    @api.doc('fetch credit report data')
    def put(self, public_id):
        """ Fetch Credit Report Data for Lead"""
        try:
            lead = get_client(public_id, client_type=ClientType.lead)
            if not lead:
                error_response = {
                    'success': False,
                    'message': 'Lead not found'
                }
                api.abort(404, **error_response)
            account, error_response = _handle_get_credit_report(
                lead, public_id)
            if not account:
                return error_response
            exists, error_response = check_existing_scrape_task(account)
            if exists:
                return error_response
            # -------------Little tweak for email-----------------
            email = account.email
            email = 'test1@consumerdirect.com'

            task = CreditReportData().launch_spider(
                account.id,
                email,
                current_app.cipher.decrypt(
                    account.password).decode()
            )

            save_changes()

            resp = {
                'messsage': 'Spider queued',
                'task_id': task.id
            }
            return resp, 200
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

    @api.doc('view credit report data')
    @api.marshal_list_with(_credit_report_data, envelope='data')
    def get(self, public_id):
        """View Credit Report Data for Lead"""
        lead = get_client(public_id, client_type=ClientType.lead)
        if not lead:
            error_response = {
                    'success': False,
                    'message': 'Lead not found'
                }
            api.abort(404, **error_response)
        data = get_report_data(lead.credit_report_account)
        return data, 200
