from app.main.model.team import Team
from .apiservice import ApiService, has_permissions
from sqlalchemy import func
from datetime import datetime

class TeamService(ApiService):
    _model = Team
    _key_field = 'id'

    def __init__(self, name=None):
        self._name = name  

    @has_permissions
    def members(self):
        team = Team.query.filter(func.lower(Team.name)==func.lower(self._name)).first()
        if team:
            return team.members
        return []

    def _parse(self, data, insert=True):
        fields = {}
        if data.get('name'):
            fields['name'] = data.get('name')
            self._name = data.get('name')
        if data.get('description'):
            fields['description'] = data.get('description')
        if data.get('is_active'):
            fields['is_active'] = data.get('is_active')
        
        fields['modified_date'] = datetime.utcnow()
        if insert is True:
            fields['creator_id'] = self._req_user.id 
            fields['created_date'] = datetime.utcnow()

        return fields

    def _queryset(self):
        return self._model.query.all()

    def _validate(self, fields):
        team = Team.query.filter(func.lower(Team.name)==func.lower(fields['name'])).first()
        if team:
            return False

        return True

