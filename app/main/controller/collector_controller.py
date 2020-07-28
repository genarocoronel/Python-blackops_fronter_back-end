from flask import request
from flask_restplus import Resource
from flask import current_app as app

from app.main.util.dto import CollectorDto
from app.main.util.decorator import (token_required, enforce_rac_policy, enforce_rac_required_roles)
from app.main.core.errors import BadRequestError, NotFoundError
from app.main.core.rac import RACRoles
from app.main.service.collector_service import get_all_collectors, create_collector, update_collector

api = CollectorDto.api
_collector = CollectorDto.collector
_collector_create = CollectorDto.collector_create

@api.route('')
class CollectorList(Resource):
    @api.doc('Creates a Debt Collector')
    @api.expect(_collector_create, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def post(self):
        """ Creates a Debt Collector """
        request_data = request.json

        try:
            collector = create_collector(request_data)

        except BadRequestError as e:
            api.abort(400, message='Error creating debt collector, {}'.format(str(e)), success=False)
        except NotFoundError as e:
            api.abort(404, message='Error creating debt collector, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to create debt collector', success=False)

        return collector, 200
    
    @api.doc('Gets a list of Debt Collectors')
    @api.marshal_list_with(_collector, envelope='data')
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def get(self):
        """ Gets a list of Debt Collectors """
        return get_all_collectors()

@api.route('/<collector_id>')
class CollectorRecord(Resource):
    @api.doc('Updates a Debt Collector') 
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN, RACRoles.DOC_PROCESS_MGR, 
        RACRoles.DOC_PROCESS_REP])
    def post(self, collector_id):
        """ Updates a Debt Collector """
        data = request.json
        try:
            collector = update_collector(collector_id, data)
            return collector, 200
        except Exception as e:
            api.abort(500, message=f'Failed to update debt collector', success=False)

