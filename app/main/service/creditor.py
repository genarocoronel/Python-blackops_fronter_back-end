from .apiservice import ApiService
from app.main.model.creditor import Creditor
from datetime import datetime

class CreditorService(ApiService):
    _model = Creditor
    _key_field   = 'id'
    _optional_fields = ['company_name', 'contact_person', 'phone', 'fax', 
                        'email', 'is_active', 'address', 'city',
                        'state', 'zipcode']
    
    def _parse(self, data, insert=True):
        fields = {}

        name = data.get('name')
        if not name:
            raise ValueError('Mandatory params not present')
        fields['name'] = name
        if insert is True:
            fields['inserted_on'] = datetime.utcnow()
        # optional fields
        for fname in optional_fields:
            if data.get(fname):
                fields[fname] = data.get(fname) 
        # updated 
        fields['updated_on'] = datetime.utcnow()

        return fields

    def _validate(self, fields, method='save'):
        if method == 'save':
            obj = self._model.query.filter_by(name=fields.get('name')).first()
            if obj:
                raise ValueError("Creditor already exists in the database.")

    def _queryset(self):
        return self._model.query.all()
