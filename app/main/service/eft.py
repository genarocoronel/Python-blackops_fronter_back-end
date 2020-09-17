from app.main.model.debt_payment import EftReturnFee
from .apiservice import ApiService
from datetime import datetime

class EftFeeService(ApiService):
    _model = EftReturnFee
    _key_field = 'id'

    def _parse(self, data, insert=True):
        fields = {}
        if data.get('code'):
            fields['code'] = data.get('code')
        if data.get('amount'):
            fields['amount'] = data.get('amount')
        fields['modified_date'] = datetime.utcnow()
        fields['agent_id'] = self._req_user.id
        # insert fields
        if insert is True:
            fields['created_date'] = datetime.utcnow() 

        return fields

    def _queryset(self):
        return self._model.query.all()

    def _validate(self, fields):
        return True
