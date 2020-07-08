import datetime
import uuid

from flask import request, send_file
from flask_restplus import Resource

from app.main import db
from app.main.model.campaign import Campaign
from app.main.model.candidate import CandidateImport, Candidate
from app.main.util.dto import CampaignDto
from app.main.service.campaign_service import CampaignService, PinnaclePhoneNumService
from app.main.util.decorator import token_required

api = CampaignDto.api
_campaign = CampaignDto.campaign
_new_campaign = CampaignDto.new_campaign
_update_campaign = CampaignDto.update_campaign


@api.route('/')
class CampaignsList(Resource):
    #@api.expect(_new_campaign, validate=True)
    @token_required
    @api.marshal_with(_campaign)
    def post(self):
        """ Create Campaign """
        try:
            payload = request.json
            cs = CampaignService()
            return cs.create(payload)

        except Exception as e:
            api.abort(500, message=str(e), success=False)

    @token_required
    @api.doc('list all campaigns')
    @api.marshal_list_with(_campaign, envelope='data')
    def get(self):
        """ List all campaigns """
        cs = CampaignService()
        campaigns = cs.get()
        return campaigns, 200


@api.route('/<campaign_id>')
@api.param('campaign_id', 'Campaign Identifier')
@api.response(404, 'Campaign not found')
class UpdateCampaign(Resource):
    #@api.expect(_update_campaign, validate=True)
    @token_required
    @api.marshal_with(_campaign)
    def put(self, campaign_id):
        """ Update Campaign Information """
        payload = request.json
        try:
            service = CampaignService()
            return service.update(campaign_id, payload)

        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/pin-phone-nums')
@api.response(404, 'Pinancele Numbers not found')
class PinnaclePhoneList(Resource):
    @token_required
    @api.doc('list all pinnacle phone nums')
    def get(self): 
        """ List all pinnacle phone nums """
        service = PinnaclePhoneNumService() 
        pp_nums = service.get()
        result = [ppn.number for ppn in pp_nums]
        
        return result, 200 


@api.route('/<campaign_id>/mailer-file')
@api.param('campaign_id', 'Campaign public id')
class GenerateCampaignMailingFile(Resource):
    def put(self, campaign_id):
        """ Generate Campaign Mailer File """
        campaign = Campaign.query.filter_by(public_id=campaign_id).first()
        if campaign.candidates.count() > 0:
            campaign.launch_task('generate_mailer_file')
            return {'success': True, 'message': 'Initiated generate mailer file'}, 200
        else:
            api.abort(404, message='Campaign does not exist', success=False)

    def get(self, campaign_id):
        """ Download Generated Campaign Mailer File """
        campaign = Campaign.query.filter_by(public_id=campaign_id).first()
        if campaign:
            return send_file(campaign.mailer_file)
        else:
            api.abort(404, message='Campaign does not exist', success=False)


@api.route('/<campaign_id>/import/<import_id>')
@api.param('campaign_id', 'Campaign public id')
@api.param('import_id', 'Candidate Import public id')
class AssignImportToCampaign(Resource):
    def put(self, campaign_id, import_id):
        """ Assign Candidate Import to Campaign """
        try:
            campaign = Campaign.query.filter_by(public_id=campaign_id).first()
            candidate_import = CandidateImport.query.filter_by(public_id=import_id).first()

            Candidate.query.filter_by(import_id=candidate_import.id).update({Candidate.campaign_id: campaign.id})
            db.session.commit()
            return {'success': True, 'message': 'Successfully assigned import to campaign'}, 200
        except Exception as e:
            api.abort(500, message=str(e), success=False)

@api.route('/status/<campaign_id>')
@api.param('campaign_id', 'Campaign public id')
class GetCampaignAssociationStatus(Resource):
    def get(self, campaign_id):
        """ Get Campaign Association Status """
        try:
            campaign = Campaign.query.filter_by(public_id=campaign_id).first()

            candidates_association = Candidate.query.filter_by(campaign_id=campaign.id).first()
            if candidates_association is None:
                return {'success': False, 'message': 'No assigned'}, 200
            else:
                return {'success': True, 'message': 'Assigned'}, 200
        except Exception as e:
            api.abort(500, message=str(e), success=False)

