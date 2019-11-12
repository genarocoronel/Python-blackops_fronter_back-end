import datetime
import uuid

from flask import request, send_file
from flask_restplus import Resource

from app.main import db
from app.main.model.campaign import Campaign
from app.main.model.candidate import CandidateImport, Candidate
from app.main.util.dto import CampaignDto

api = CampaignDto.api
_campaign = CampaignDto.campaign
_new_campaign = CampaignDto.new_campaign
_update_campaign = CampaignDto.update_campaign


@api.route('/')
class CampaignsList(Resource):
    @api.expect(_new_campaign, validate=True)
    def post(self):
        """ Create Campaign """
        try:
            payload = request.json

            new_campaign = Campaign(
                public_id=str(uuid.uuid4()),
                name=payload.get('name'),
                description=payload.get('description'),
                phone=payload.get('phone'),
                job_number=payload.get('job_number'),
                offer_expire_date=payload.get('offer_expire_date'),
                mailing_date=payload.get('mailing_date'),
                inserted_on=datetime.datetime.utcnow()
            )
            db.session.add(new_campaign)
            db.session.commit()
            return {'success': True, 'message': 'Successfully created campaign'}, 201

        except Exception as e:
            api.abort(500, message=str(e), success=False)

    @api.doc('list all campaigns')
    @api.marshal_list_with(_campaign, envelope='data')
    def get(self):
        """ List all campaigns """
        campaigns = Campaign.query.all()
        return campaigns, 200


@api.route('/<campaign_id>')
@api.param('campaign_id', 'Campaign Identifier')
@api.response(404, 'Campaign not found')
class UpdateCampaign(Resource):
    @api.expect(_update_campaign, validate=True)
    def put(self, campaign_id):
        """ Update Campaign Information """
        payload = request.json
        try:
            campaign = Campaign.query.filter_by(public_id=campaign_id).first()
            campaign.name = payload.get('name') or campaign.name
            campaign.description = payload.get('description') or campaign.description
            campaign.phone = payload.get('phone') or campaign.phone
            campaign.job_number = payload.get('job_number') or campaign.job_number
            campaign.mailing_date = payload.get('mailing_date') or campaign.mailing_date
            campaign.offer_expire_date = payload.get('offer_expire_date') or campaign.offer_expire_date
            db.session.commit()

            return {'success': True, 'message': 'Successfully updated campaign'}, 200

        except Exception as e:
            api.abort(500, message=str(e), success=False)


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
