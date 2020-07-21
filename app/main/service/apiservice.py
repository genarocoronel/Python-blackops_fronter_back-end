from functools import wraps
from datetime import datetime

from app.main.core.rac import RACRoles
from ..core.rac import RACMgr
from app.main import db


def has_permissions(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        # instance
        roles_to_enforce = args[0]._permissions
        if not RACMgr.enforce_policy_user_has_role(roles_to_enforce):
            return 'You do not have permissions to access this resource or action', 403
        return func(*args, **kwargs)

    return decorated


# CRUD operations 
class ApiService(object):
    _permissions = []
    _model = None 
    _key_field = 'id'

    @has_permissions
    def create(self, data):
        if not self._model:
            raise ValueError("Not a valid service")    
        # extract attributes
        attrs = self._parse(data)
        # validate
        self._validate(attrs)

        obj = self._model()
        for attr in attrs:
            if hasattr(obj, attr):
                setattr(obj, attr, attrs.get(attr)) 

        db.session.add(obj)
        db.session.commit()
        return obj 

    @has_permissions
    def get(self):
        records = self._queryset()
        return records

    @has_permissions
    def update(self, key, data):
        if not self._model:
            raise ValueError("Not a valid service")

        kwargs = {}
        kwargs[self._key_field] = key
        obj = self._model.query.filter_by(**kwargs).first()
        if not obj:
            raise ValueError("Record not found")

        # extract attributes
        attrs = self._parse(data, insert=False) 
        for attr in attrs:
            if hasattr(obj, attr):
                setattr(obj, attr, attrs.get(attr))

        db.session.commit()

    @has_permissions
    def delete(self, key):
        if not self._model:
             raise ValueError("Not a valid service")

        kwargs = {}
        kwargs[self._key_field] = key
        obj = self._model.query.filter_by(**kwargs).first()
        if not obj:
            raise ValueError("Record not found")

        db.session.delete(obj)
        db.session.commit()

