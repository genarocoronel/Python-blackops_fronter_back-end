import os

from flask import request, current_app
from flask_restplus import Resource
from werkzeug.utils import secure_filename

from app.main.config import upload_location
from app.main.model.candidate import CandidateImport
from app.main.model.credit_report_account import CreditReportSignupStatus, CreditReportData, CreditReportAccount
from app.main.service.auth_helper import Auth
from app.main.service.candidate_service import save_new_candidate_import, save_changes, get_all_candidate_imports, \
    get_candidate, get_all_candidates, update_candidate
from app.main.service.credit_report_account_service import\
    save_new_credit_report_account, update_credit_report_account,\
    get_report_data
from app.main.service.smartcredit_service import start_signup, LockedException, create_customer, \
    get_id_verification_question, answer_id_verification_questions, update_customer, does_email_exist, \
    complete_credit_account_signup
from ..util.dto import CandidateDto

api = CandidateDto.api
_candidate_upload = CandidateDto.candidate_upload
_import = CandidateDto.imports
_new_credit_report_account = CandidateDto.new_credit_report_account
_update_credit_report_account = CandidateDto.update_credit_report_account
_credit_account_verification_answers = CandidateDto.account_verification_answers
_candidate = CandidateDto.candidate
_credit_report_data = CandidateDto.credit_report_data
_update_candidate = CandidateDto.update_candidate


@api.route('/')
class GetCandidates(Resource):
    @api.doc('get all candidates')
    @api.marshal_list_with(_candidate, envelope='data')
    def get(self):
        """ Get all Candidates """
        candidates = get_all_candidates()
        return candidates, 200


@api.route('/<candidate_id>')
@api.response(404, 'Candidate not found')
class UpdateCandidate(Resource):
    @api.doc('get candidate')
    @api.marshal_with(_candidate)
    def get(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        return candidate, 200

    @api.doc('update candidate')
    @api.expect(_update_candidate, validate=True)
    def put(self, public_id):
        return update_candidate(public_id, request.json)


@api.route('/upload')
class CandidateUpload(Resource):
    @api.doc('create candidates from file')
    @api.expect(_candidate_upload, validate=True)
    def post(self):
        """ Creates Candidates from file """

        args = _candidate_upload.parse_args()
        file = args['csv_file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_location, filename)
            file.save(file_path)

            candidate_import = save_new_candidate_import(dict(file_path=file_path))
            task = candidate_import.launch_task('parse_candidate_file',
                                                'Parse uploaded candidate file and load db with entries')

            save_changes()

            resp = {'task_id': task.id}
            return resp, 200

        else:
            return {'status': 'failed', 'message': 'No file was provided'}, 409


@api.route('/imports')
class CandidateImports(Resource):
    @api.doc('retrieve all imports efforts')
    @api.marshal_list_with(_import, envelope='data')
    def get(self):
        """ Get all Candidate Imports """
        imports = get_all_candidate_imports()
        return imports, 200


@api.route('/imports/<public_id>')
@api.param('public_id', 'The Candidate Import Identifier')
@api.response(404, 'Candidate Import not found')
class CandidateImportRecords(Resource):
    @api.doc('retrieve candidate import information')
    @api.marshal_with(_import)
    def get(self, public_id):
        """ Get Candidate Import Information """
        candidate_import = CandidateImport.query.filter_by(public_id=public_id).first()
        candidate_import.tasks.all()
        if candidate_import:
            return candidate_import, 200
        else:
            response_object = {
                'success': False,
                'message': 'Candidate Import does not exist'
            }
            api.abort(404, **response_object)


def _handle_get_candidate(candidate_public_id):
    candidate = get_candidate(candidate_public_id)
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
    if not account or account.public_id != account_public_id:
        response_object = {
            'success': False,
            'message': 'Credit Report Account does not exist'
        }
        return None, (response_object, 404)
    else:
        return account, None


@api.route('/<candidate_public_id>/credit-report/account')
@api.param('candidate_public_id', 'The Candidate Identifier')
class CreateCreditReportAccount(Resource):
    @api.doc('create credit report account')
    @api.expect(_new_credit_report_account, validate=True)
    def post(self, candidate_public_id):
        """ Create Credit Report Account """
        request_data = request.json

        # TODO: retrieve campaign information for candidate
        campaign_data = {'ad_id': 5000, 'affiliate_id': 1662780, 'campaign_id': 'ABR:DBL_OD_WOULDYOULIKETOADD_041615'}
        campaign_data.update({'channel': 'paid'})

        try:
            candidate, error_response = _handle_get_candidate(candidate_public_id)
            if not candidate:
                api.abort(404, **error_response)

            # look for existing credit report account
            credit_report_account = candidate.credit_report_account
            if not credit_report_account:
                signup_data = start_signup(campaign_data)
                credit_report_account = save_new_credit_report_account(signup_data, candidate,
                                                                       CreditReportSignupStatus.INITIATING_SIGNUP)

            if credit_report_account.status == CreditReportSignupStatus.ACCOUNT_CREATED:
                response_object = {
                    'success': False,
                    'message': 'Credit Report account already exists'
                }
                return response_object, 409

            email_exists, error = does_email_exist(request_data.get('email'), credit_report_account.tracking_token)
            if email_exists or error:
                response_object = {
                    'success': False,
                    'message': error or 'Email already exists'
                }
                return response_object, 409

            password = Auth.generate_password()
            request_data.update(dict(password=password))
            new_customer = create_customer(request_data, credit_report_account.tracking_token, sponsor_code='BTX5DY2SZK')

            credit_report_account.password = password
            credit_report_account.customer_token = new_customer.get('customerToken')
            credit_report_account.financial_obligation_met = new_customer.get('isFinancialObligationMet')
            credit_report_account.plan_type = new_customer.get('planType')
            credit_report_account.status = CreditReportSignupStatus.ACCOUNT_CREATED
            update_credit_report_account(credit_report_account)

            response_object = {
                'success': True,
                'message': f'Successfully created credit report account with {credit_report_account.provider}',
                'public_id': credit_report_account.public_id
            }
            return response_object, 201

        except LockedException as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 409
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/<candidate_public_id>/credit-report/account/password')
@api.param('candidate_public_id', 'The Candidate Identifier')
class CreditReportAccountPassword(Resource):
    @api.doc('credit report account password')
    def get(self, candidate_public_id):
        """ Retrieve Candidate Credit Report Account Password"""
        try:
            candidate, error_response = _handle_get_candidate(candidate_public_id)
            if not candidate:
                api.abort(404, **error_response)

            credit_report_account = candidate.credit_report_account
            if not credit_report_account:
                response_object = {
                    'success': False,
                    'message': 'No Credit Report Account exists'
                }
                return response_object, 404

            response_object = {
                'success': True,
                'password': current_app.cipher.decrypt(credit_report_account.password).decode()
            }
            return response_object, 200
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/<candidate_public_id>/credit-report/account/<public_id>')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class UpdateCreditReportAccount(Resource):
    @api.doc('update credit report account')
    @api.expect(_update_credit_report_account, validate=True)
    def put(self, candidate_public_id, public_id):
        """ Update Credit Report Account """
        try:
            candidate, error_response = _handle_get_candidate(candidate_public_id)
            if not candidate:
                api.abort(404, **error_response)

            account, error_response = _handle_get_credit_report(candidate, public_id)
            if not account:
                return error_response

            data = request.json
            data['ip_address'] = request.remote_addr
            data['terms_confirmed'] = True
            update_customer(account.customer_token, data, account.tracking_token)

            response_object = {
                'success': True,
                'message': 'Successfully updated credit report account'
            }
            return response_object, 200

        except LockedException as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 409
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/<candidate_public_id>/credit-report/account/<public_id>/verification-questions')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class CreditReporAccounttVerification(Resource):
    @api.doc('get verification questions')
    def get(self, candidate_public_id, public_id):
        """ Get Account Verification Questions """
        try:
            candidate, error_response = _handle_get_candidate(candidate_public_id)
            if not candidate:
                api.abort(404, **error_response)

            account, error_response = _handle_get_credit_report(candidate, public_id)
            if not account:
                return error_response

            questions = get_id_verification_question(account.customer_token, account.tracking_token)
            account.status = CreditReportSignupStatus.ACCOUNT_VALIDATING
            update_credit_report_account(account)

            return questions, 200

        except LockedException as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 409
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

    @api.doc('submit answers to verification questions')
    @api.expect(_credit_account_verification_answers, validate=False)
    def put(self, candidate_public_id, public_id):
        """ Submit Account Verification Answers """
        try:
            candidate, error_response = _handle_get_candidate(candidate_public_id)
            if not candidate:
                api.abort(404, **error_response)

            account, error_response = _handle_get_credit_report(candidate, public_id)
            if not account:
                return error_response

            data = request.json
            answer_id_verification_questions(account.customer_token, data, account.tracking_token)
            account.status = CreditReportSignupStatus.ACCOUNT_VALIDATED
            update_credit_report_account(account)

            response_object = {
                'success': True,
                'message': 'Successfully submitted verification answers'
            }
            return response_object, 200

        except LockedException as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 409
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/<candidate_public_id>/credit-report/account/<credit_account_public_id>/complete')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CompleteCreditReportAccount(Resource):
    @api.doc('complete credit report account signup')
    def put(self, candidate_public_id, credit_account_public_id):
        """ Complete Credit Report Account Sign Up"""
        try:
            candidate, error_response = _handle_get_candidate(candidate_public_id)
            if not candidate:
                api.abort(404, **error_response)

            account, error_response = _handle_get_credit_report(candidate, credit_account_public_id)
            if not account:
                return error_response

            complete_credit_account_signup(account.customer_token, account.tracking_token)
            account.status = CreditReportSignupStatus.FULL_MEMBER
            update_credit_report_account(account)

            response_object = {
                'success': True,
                'message': 'Successfully completed credit account signup'
            }
            return response_object, 200

        except LockedException as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 409
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/<public_id>/credit-report/run_spider')
@api.param('public_id', 'The Candidate Identifier')
class ScrapeCreditReportAccount(Resource):
    @api.doc('scrape credit report')
    def put(self, public_id):
        """ Scrape Credit Report """
        try:
            candidate, error_response = _handle_get_candidate(public_id)
            if not candidate:
                api.abort(404, **error_response)
            account, error_response = _handle_get_credit_report(candidate, public_id)
            if not account:
                return error_response

            # --------Need to update this email---------
            email = 'test1@consumerdirect.com'
            task = CreditReportData().launch_spider(
                'run',
                'Scrapes credit report for given candidate',
                public_id,
                candidate.email,
                current_app.cipher.decrypt(
                    account.password).decode()
            )

            save_changes()

            resp = {
                'messsage': 'Spider queued',
                'task_id': task.id
            }
            return resp, 200
        except LockedException as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 409
        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500


@api.route('/<public_id>/credit-report/report_data')
@api.param('public_id', 'The Candidate Identifier')
class ScrapeCreditReportData(Resource):
    @api.doc('View credit report data')
    @api.marshal_list_with(_credit_report_data, envelope='data')
    def get(self, public_id):
        """View Credit Report Data"""
        data = get_report_data(public_id)
        return data, 200
