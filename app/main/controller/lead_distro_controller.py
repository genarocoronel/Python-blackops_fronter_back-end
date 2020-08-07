from flask import Flask, request
from flask_restplus import Resource
from app.main.util.dto import LeadDistroDto
from app.main.util.decorator import token_required
from app.main.service.lead_distro import LeadDistroSvc
from app.main.model import Language

api = LeadDistroDto.api
_profile = LeadDistroDto.profile

@api.route('/agents')
class LeadDistroAgentList(Resource):
    @api.doc('Fetches all sales agents by priority')
    @api.marshal_with(_profile)
    @token_required
    def get(self):
        try:
            lang = request.args.get('language', Language.ENGLISH.name)
            svc = LeadDistroSvc(lang)
            return svc.get()

        except Exception as e:
            api.abort(500, message=str(e), success=False)

    @api.doc('Updates lead distribution parameters of all sales agents')
    @token_required
    def put(self):
        try:
            data = request.json
            lang = data.get('language')
            print(data)
            svc  = LeadDistroSvc(lang)
            return svc.update(data)

        except Exception as e:
            api.abort(500, message=str(e), success=False)
   
    
