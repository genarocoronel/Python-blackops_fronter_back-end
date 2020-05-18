import uuid
import datetime
from app.main import db
from app.main.core.errors import BadRequestError
from app.main.core.auth import Auth
from app.main.model.portal_user import PortalUser


def get_portal_user_by_id(id):
    return PortalUser.query.filter_by(id=id).first()


def get_portal_user_by_pubid(public_id):
    return PortalUser.query.filter_by(public_id=public_id).first()


def get_portal_user_by_email(email):
    return PortalUser.query.filter_by(email=email).first()


def create_portal_user(email, username, password, client_id, is_disabled=False):
    if get_portal_user_by_email(email):
        raise NoDuplicateAllowed('A Portal User with that email already exists.')
    else:
        user = PortalUser(
            public_id = str(uuid.uuid4()),
            email = email,
            username = username,
            password = password,
            client_id = client_id,
            is_disabled = is_disabled,
            registered_on = datetime.datetime.utcnow()
        )
        _save_changes(user)

    return user


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()