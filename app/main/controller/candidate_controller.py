import os

from flask import current_app as app
from flask import request
from flask_restplus import Resource
from werkzeug.utils import secure_filename

from app.main.util.decorator import (token_required, enforce_rac_policy, enforce_rac_required_roles)
from app.main.config import upload_location
from app.main.controller import _convert_payload_datetime_values
from app.main.core.errors import (BadRequestError, ServiceProviderError, ServiceProviderLockedError)
from app.main.core.rac import RACRoles
from app.main.core.types import CustomerType
from app.main.model.candidate import CandidateImport
from app.main.service.candidate_service import (save_new_candidate_import, save_changes, get_all_candidate_imports,
                                                get_candidate, update_candidate, get_candidate_employments, update_candidate_employments,
                                                update_candidate_contact_numbers, get_candidate_contact_numbers,
                                                get_candidate_income_sources,
                                                update_candidate_income_sources, get_candidate_monthly_expenses,
                                                update_candidate_monthly_expenses,
                                                get_candidate_addresses, update_candidate_addresses, convert_candidate_to_lead,
                                                delete_candidates, candidate_filter, assign_openerrep)
from app.main.service.user_service import get_a_user
from app.main.service.communication_service import parse_communication_types, date_range_filter, \
    get_communication_records, get_candidate_voice_communication, create_presigned_url
from app.main.service.credit_report_account_service import (creport_account_signup, update_credit_report_account,
                                                            get_verification_questions, answer_verification_questions, complete_signup,
                                                            get_security_questions,
                                                            register_fraud_insurance, get_account_password, pull_credit_report)
from app.main.util.dto import CandidateDto
from app.main.util.parsers import filter_request_parse

api = CandidateDto.api
_candidate_upload = CandidateDto.candidate_upload
_import = CandidateDto.imports
_new_credit_report_account = CandidateDto.new_credit_report_account
_update_credit_report_account = CandidateDto.update_credit_report_account
_credit_account_verification_answers = CandidateDto.account_verification_answers
_candidate = CandidateDto.candidate
_candidate_pagination = CandidateDto.candidate_pagination
_update_candidate = CandidateDto.update_candidate
_candidate_employment = CandidateDto.candidate_employment
_update_candidate_employment = CandidateDto.update_candidate_employment
_update_candidate_number = CandidateDto.update_candidate_number
_candidate_number = CandidateDto.candidate_number
_candidate_income = CandidateDto.candidate_income
_communication = CandidateDto.candidate_communication
_update_candidate_income = CandidateDto.update_candidate_income
_candidate_monthly_expense = CandidateDto.candidate_monthly_expense
_update_candidate_monthly_expense = CandidateDto.update_candidate_monthly_expense
_candidate_address = CandidateDto.candidate_address
_update_candidate_addresses = CandidateDto.update_candidate_addresses


#### request params
# @_limit result set max limit
# @_order direction 'asc' or 'desc'
# @_sort sort field
# @_page_number pagination page number
@api.route('/')
class GetCandidates(Resource):
    @api.doc('get candidates with pagination info')
    @api.marshal_with(_candidate_pagination)
    def get(self):
        """ Get all Candidates """
        limit = request.args.get('_limit', None)
        order = request.args.get('_order', None)
        sort = request.args.get('_sort', None)
        pagenum = request.args.get('_page_number', None)

        kwargs = {}

        if limit is not None:
            kwargs['limit'] = int(limit)
        if sort is not None:
            kwargs['sort_col'] = sort
        if order is not None:
            kwargs['order'] = order
        if pagenum is not None:
            kwargs['pageno'] = int(pagenum)
        result = candidate_filter(**kwargs)
        return result, 200

    @api.doc('delete candidates')
    def delete(self):
        """Delete Candidates"""
        request_data = request.json
        delete_candidates(request_data.get('ids'))
        return dict(success=True), 200


#### request params
# @_limit result set max limit
# @_order direction 'asc' or 'desc'
# @_sort sort field
# @_page_number pagination page number
# @_q string search field/fields
# @_dt datetime search field/fields
# @_search string Search value
# @_from if date filter is enabled - From date
# @_to if date filter is enabled - To date
@api.route('/filter')
class CandidateFilter(Resource):
    @api.doc('Candidates filter with pagination info')
    @api.marshal_with(_candidate_pagination)
    def get(self):
        """ Get filtered Candidates """
        # filter args
        fargs = filter_request_parse(request)
        print("======", fargs)
        result = candidate_filter(**fargs)
        return result, 200


@api.route('/<candidate_id>')
@api.param('candidate_id', 'Candidate public identifier')
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
    def put(self, candidate_id):
        data = request.json
        _convert_payload_datetime_values(data, 'dob')
        return update_candidate(candidate_id, data)


@api.route('/<public_id>/assign/<user_public_id>/')
@api.param('public_id', 'The Candidate Identifier')
@api.response(404, 'Candidate not found')
class CandidateAssignment(Resource):
    @api.doc('Assigns a Candidate to a Opener Rep user')
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.OPENER_MGR])
    def put(self, public_id, user_public_id):
        """ Assigns a Candidate to a Opener Rep user """
        candidate, error_response = _handle_get_candidate(public_id)
        if not candidate:
            api.abort(404, **error_response)
        
        asignee = get_a_user(user_public_id)
        if not asignee:
            api.abort(404, message='That Opener Rep could not be found.', success=False)

        try:
            assign_openerrep(candidate, asignee)

        except Exception as e:
            api.abort(500, message=f'Failed to assign a Opener Rep for this Candidate. Error: {e}', success=False)

        response_object = {
            'success': True,
            'message': f'Successfully assigned this Candidate to Opener Rep with ID {user_public_id}.',
        }
        return response_object, 200


@api.route('/<candidate_id>/income-sources')
@api.param('candidate_id', 'Candidate public identifier')
@api.response(404, 'Candidate not found')
class CandidateIncomeSources(Resource):
    @api.doc('get candidate income sources')
    @api.marshal_list_with(_candidate_income)
    def get(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_candidate_income_sources(candidate)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update candidate income sources')
    @api.expect([_update_candidate_income], validate=True)
    def put(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            numbers = request.json
            result, err_msg = update_candidate_income_sources(candidate, numbers)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<candidate_id>/monthly-expenses')
@api.param('candidate_id', 'Candidate public identifier')
@api.response(404, 'Candidate not found')
class CandidateMonthlyExpenses(Resource):
    @api.doc('get candidate monthly expenses')
    @api.marshal_list_with(_candidate_monthly_expense)
    def get(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_candidate_monthly_expenses(candidate)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update candidate monthly expenses')
    @api.expect([_update_candidate_monthly_expense], validate=True)
    def put(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            expenses = request.json
            result, err_msg = update_candidate_monthly_expenses(candidate, expenses)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<candidate_id>/contact_numbers')
@api.param('candidate_id', 'Candidate public identifier')
@api.response(404, 'Candidate not found')
class CandidateContactNumbers(Resource):
    @api.doc('get candidate contact numbers')
    @api.marshal_list_with(_candidate_number)
    def get(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_candidate_contact_numbers(candidate)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update candidate contact numbers')
    @api.expect([_update_candidate_number], validate=True)
    def put(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            numbers = request.json
            result, err_msg = update_candidate_contact_numbers(candidate, numbers)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<candidate_id>/communications')
class CandidateCommunications(Resource):
    @api.marshal_list_with(_communication, envelope='data')
    @api.param('_dt', 'Comma separated date fields to be filtered')
    @api.param('_from', 'Start date of communications to query (YYYY-MM-DD)')
    @api.param('_to', 'End date of communications to query (YYYY-MM-DD)')
    @api.param('type', "Default is 'all'. Options are 'call', 'voicemail', or 'sms'")
    def get(self, candidate_id):
        """ Get all forms of communication for given client """
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            filter = filter_request_parse(request)
            comm_types_set = parse_communication_types(request)

            date_range_filter(filter)

            date_filter_fields = filter.get('dt_fields', [])
            result = get_communication_records(filter, comm_types_set, candidates=candidate, date_filter_fields=date_filter_fields)

            return sorted(result, key=lambda record: record.receive_date, reverse=True)


@api.route('/<candidate_id>/communications/<communication_id>/file')
class CandidateCommunicationsFile(Resource):
    @api.doc('Get communications audio file')
    def get(self, candidate_id, communication_id):
        """ Get voice communication file url """
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)

        voice_communication = get_candidate_voice_communication(candidate, communication_id)
        if not voice_communication:
            api.abort(404, message='Voice communication not found', success=False)
        else:
            expiration_seconds = app.s3_signed_url_timeout_seconds
            file_url = create_presigned_url(voice_communication, expiration=expiration_seconds)
            response_object = {
                'success': True,
                'message': f'File URL will expire in {expiration_seconds / 60} minutes.',
                'file_url': file_url
            }
            return response_object, 200


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
        # candidate_import.tasks.all()
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

    return candidate, None


def _handle_get_credit_report(candidate):
    account = candidate.credit_report_account
    if not account:
        response_object = {
            'success': False,
            'message': 'Credit Report Account does not exist'
        }
        return None, response_object
    else:
        return account, None


@api.route('/<candidate_public_id>/credit-report/account')
@api.param('candidate_public_id', 'The Candidate Identifier')
class CreateCreditReportAccount(Resource):
    @api.doc('Create credit report account for Candidate. This is Step #1 in process.')
    @api.expect(_new_credit_report_account, validate=True)
    def post(self, candidate_public_id):
        request_data = request.json

        candidate, error_response = _handle_get_candidate(candidate_public_id)
        if not candidate:
            api.abort(404, **error_response)

        try:
            app.logger.info('Received request to signup Candidate for a Credit Report Account.')
            creport_acc = creport_account_signup(request_data, candidate, CustomerType.CANDIDATE)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot sign up for new Credit Account due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot sign up for new Credit Account due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': f'Successfully created credit report account with {creport_acc.provider}',
            'public_id': creport_acc.public_id
        }
        return response_object, 201


@api.route('/<candidate_public_id>/credit-report/account/<public_id>')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class UpdateCreditReportAccount(Resource):
    @api.doc('update credit report account. This is step #2, and #4 in the process.')
    @api.expect(_update_credit_report_account, validate=True)
    def put(self, candidate_public_id, public_id):
        """ Update Credit Report Account """
        candidate, error_response = _handle_get_candidate(candidate_public_id)
        if not candidate:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(candidate)
        if not account:
            return error_response

        request_data = request.json
        relevant_data = None

        if 'security_question_id' in request_data:
            relevant_data = {
                'security_question_id': request_data['security_question_id'],
                'security_question_answer': request_data['security_question_answer'],
                'ssn': request_data['ssn']
            }
        else:
            relevant_data = request_data

        relevant_data['ip_address'] = request.remote_addr
        relevant_data['terms_confirmed'] = True

        try:
            app.logger.info(f"Received request to update Credit Report account for Candidate with ID: {candidate_public_id}")
            update_credit_report_account(account, relevant_data)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to update Credit Account, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot update Credit Account due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot update Credit Account due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': 'Successfully updated credit report account'
        }
        return response_object, 200


@api.route('/<candidate_public_id>/credit-report/account/<credit_account_public_id>/security-questions')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CreditReportAccountSecurityQuestions(Resource):
    @api.doc('get credit report account security questions. This is step #3 in process.')
    def get(self, candidate_public_id, credit_account_public_id):
        """ Get Available Security Questions"""
        candidate, error_response = _handle_get_candidate(candidate_public_id)
        if not candidate:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(candidate)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to get Credit Account Security Questions.')
            questions = get_security_questions(account)

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get credit account security questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get credit account security questions due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        return questions, 200


@api.route('/<candidate_public_id>/credit-report/account/<public_id>/verification-questions')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('public_id', 'The Credit Report Account Identifier')
class CreditReporAccounttVerification(Resource):
    @api.doc('get verification questions. Step #5 in process.')
    def get(self, candidate_public_id, public_id):
        """ Get Account Verification Questions """
        candidate, error_response = _handle_get_candidate(candidate_public_id)
        if not candidate:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(candidate)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to get Credit Account ID Verification Questions.')
            questions = get_verification_questions(account)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to get verification questions, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get verification questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot get verification questions due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        return questions, 200

    @api.doc('submit answers to verification questions. Step #6 in process.')
    @api.expect(_credit_account_verification_answers, validate=False)
    def put(self, candidate_public_id, public_id):
        """ Submit Account Verification Answers """
        candidate, error_response = _handle_get_candidate(candidate_public_id)
        if not candidate:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(candidate)
        if not account:
            return error_response

        data = request.json

        try:
            app.logger.info('Received request to answer Credit Account Verification Questions.')
            answer_verification_questions(account, data)

        except BadRequestError as e:
            response_object = {
                'success': False,
                'message': f'There was an issue with data in your request to submit verification questions, {str(e)}'
            }
            return response_object, 400

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot submit verification questions due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot submit verification questions due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': 'Successfully submitted verification answers'
        }
        return response_object, 200


# TODO: consider removing the `credit_account_public_id` from URI since it is only 1-to-1 relationship in data model
@api.route('/<candidate_public_id>/credit-report/account/<credit_account_public_id>/complete')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CompleteCreditReportAccoxnt(Resource):
    @api.doc('complete credit report account signup. Step #7 and final step in process.')
    def put(self, candidate_public_id, credit_account_public_id):
        """ Complete Credit Report Account Sign Up"""
        candidate, error_response = _handle_get_candidate(candidate_public_id)
        if not candidate:
            api.abort(404, **error_response)

        account, error_response = _handle_get_credit_report(candidate)
        if not account:
            return error_response

        try:
            app.logger.info('Received request to complete Credit Report account signup.')
            complete_signup(account)

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot complete credit account signup due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot complete credit account signup due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': 'Successfully completed credit account signup'
        }
        return response_object, 200

    # @api.doc('submit answer to security question')
    # @api.expect(_update_credit_report_account, validate=True)
    # def put(self, candidate_public_id, credit_account_public_id):
    #     """ Submit Answer to Security Question """
    #     try:
    #         candidate, error_response = _handle_get_candidate(candidate_public_id)
    #         if not candidate:
    #             api.abort(404, **error_response)

    #         account, error_response = _handle_get_credit_report(candidate)
    #         if not account:
    #             return error_response

    #         data = request.json
    #         update_customer(account.customer_token, data, account.tracking_token)
    #         account.status = CreditReportSignupStatus.FULL_MEMBER_LOGIN
    #         update_credit_report_account(account)

    #         response_object = {
    #             'success': True,
    #             'message': 'Successfully submitted security question answer'
    #         }
    #         return response_object, 200

    #     except ServiceProviderLockedError as e:
    #         response_object = {
    #             'success': False,
    #             'message': 'Cannot sign up for new Credit Account due to a service provider Locked issue, {str(e)}'
    #         }
    #         return response_object, 409
    #     except Exception as e:
    #         response_object = {
    #             'success': False,
    #             'message': str(e)
    #         }
    #         return response_object, 500


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

            pwd = get_account_password(credit_report_account)

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'password': pwd
        }
        return response_object, 200


@api.route('/<candidate_public_id>/credit-report/account/<credit_account_public_id>/fraud-insurance/register')
@api.param('candidate_public_id', 'The Candidate Identifier')
@api.param('credit_account_public_id', 'The Credit Report Account Identifier')
class CandidateFraudInsurance(Resource):
    @api.doc('register candidate for fraud insurance')
    def post(self, candidate_public_id, credit_account_public_id):
        candidate, error_response = _handle_get_candidate(candidate_public_id)
        if not candidate:
            api.abort(404, **error_response)

        credit_report_account, error_response = _handle_get_credit_report(candidate)
        if not credit_report_account:
            api.abort(404, **error_response)

        if credit_report_account.registered_fraud_insurance:
            response_object = {
                'success': False,
                'message': 'Credit account already registered for fraud insurance'
            }
            return response_object, 409

        try:
            result = register_fraud_insurance(credit_report_account)

        except ServiceProviderLockedError as e:
            response_object = {
                'success': False,
                'message': f'Cannot register for fraud insurance due to a service provider Locked issue, {str(e)}'
            }
            return response_object, 409

        except ServiceProviderError as e:
            response_object = {
                'success': False,
                'message': f'Cannot register for fraud insurance due to a service provider issue, {str(e)}'
            }
            return response_object, 502

        except Exception as e:
            response_object = {
                'success': False,
                'message': str(e)
            }
            return response_object, 500

        response_object = {
            'success': True,
            'message': result
        }
        return response_object, 200


@api.route('/<candidate_id>/employments')
@api.param('candidate_id', 'Candidate public identifier')
@api.response(404, 'Candidate not found')
class CandidateEmployments(Resource):
    @api.doc('get candidate employments')
    @api.marshal_list_with(_candidate_employment)
    def get(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_candidate_employments(candidate)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200

    @api.doc('update candidate employment')
    @api.expect([_update_candidate_employment], validate=False)
    def put(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            employments = request.json
            _convert_payload_datetime_values(employments, 'start_date', 'end_date')
            result, err_msg = update_candidate_employments(candidate, employments)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return dict(success=True, **result), 200


@api.route('/<candidate_id>/addresses')
@api.param('candidate_id', 'Candidate public identifier')
@api.response(404, 'Candidate not found')
class CandidateAddresses(Resource):
    @api.response(200, 'Address successfully created')
    @api.doc('create new address')
    @api.expect([_update_candidate_addresses], validate=True)
    def put(self, candidate_id):
        """ Creates new Address """
        addresses = request.json
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        return update_candidate_addresses(candidate, addresses)

    @api.doc('get candidate addresses')
    @api.marshal_list_with(_candidate_address)
    def get(self, candidate_id):
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)
        else:
            result, err_msg = get_candidate_addresses(candidate)
            if err_msg:
                api.abort(500, err_msg)
            else:
                return result, 200


@api.route('/<candidate_id>/submit_to_underwriter')
@api.param('candidate_id', 'Candidate public identifier')
@api.response(404, 'Candidate not found')
class CandidateToLead(Resource):
    @api.response(200, 'Address successfully created')
    @api.doc('Convert a candidate to a lead')
    def post(self, candidate_id):
        """ Convert Candidate to Lead """
        candidate, error_response = _handle_get_candidate(candidate_id)
        if not candidate:
            api.abort(404, **error_response)

        credit_report_account = candidate.credit_report_account
        if not credit_report_account:
            api.abort(404, "No credit report account associated with candidate. Create SC account first.")

        app.logger.api("Received request to STU and convert a Candidate to Lead")
        convert_candidate_to_lead(candidate)

        app.logger.api("Requesting Credit Report pull for converted Lead")
        pull_credit_report(credit_report_account)

        return {"success": True, "message": "Successfully submitted candidate to underwriter"}, 200
