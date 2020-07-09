from datetime import datetime
import uuid

from app.main.model.campaign import Campaign, MarketingModel, MailType, PinnaclePhoneNumber
from .apiservice import ApiService

class CampaignService(ApiService):
    _model = Campaign
    _key_field   = 'public_id'
    
    def _parse(self, data):
        ## validate if necessary
        mkt_type = data.get('marketing_type')
        mm = MarketingModel[mkt_type]
        mail_type = data.get('mail_type')
        mt = MailType[mail_type]
        name = data.get('name')
        num_pieces = data.get('num_mail_pieces')

        min_debt = data.get('min_debt')
        max_debt = data.get('max_debt')
        debt_range = {
            'min': min_debt if min_debt else 0,
            'max': max_debt if max_debt else 0,
        }

        mail_dtime = datetime.strptime(data.get('mailing_date'), '%Y-%m-%d')
        month_word = mail_dtime.strftime("%B")
        job_num = f'{mkt_type}_{month_word}{mail_dtime.day}{mail_dtime.year}_{mail_type}_{num_pieces}_{min_debt}-{max_debt}'
           
        pin_phone_no = data.get('pinnacle_phone')
        ppn = PinnaclePhoneNumber.query.filter_by(number=pin_phone_no).first()
        if not ppn:
            # should we create new entry ??
            raise ValueError("Pinnacle Phone Number not present")

        fields = {
            'public_id': str(uuid.uuid4()),
            'name': name,
            'description': data.get('description'),
            'phone': data.get('phone'),
            'job_number': job_num,
            'offer_expire_date': data.get('offer_expire_date'),
            'mailing_date': data.get('mailing_date'),
            'pinnacle_phone_num_id': ppn.id, 
            'marketing_model': mm.name,
            'mail_type': mt.name, 
            'num_mail_pieces': num_pieces,
            'cost_per_piece': data.get('cost_per_piece'),
            'est_debt_range': debt_range,
            'inserted_on': datetime.utcnow(),
        }

        return fields

    def _validate(self, fields, method='save'): 
        if method == 'save':
            obj = self._model.query.filter_by(name=fields.get('name')).first()     
            if obj:
                raise ValueError("Campaign name already exists in the database.")
    

    def _queryset(self):
        return self._model.query.all()

class PinnaclePhoneNumService(ApiService):
    _model = PinnaclePhoneNumber
    
    def _queryset(self):
        return self._model.query.all()
