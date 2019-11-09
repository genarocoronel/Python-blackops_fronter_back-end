from flask_restplus import Resource

from app.main.model.campaign import Campaign
from app.main.util.dto import CampaignDto

api = CampaignDto.api
_campaign = CampaignDto.campaign


@api.route('/')
class CampaignsList(Resource):
    @api.doc('list all campaigns')
    @api.marshal_list_with(_campaign, envelope='data')
    def get(self):
        """ List all campaigns """
        campaigns = Campaign.query.all()
        return campaigns, 200
