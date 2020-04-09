import uuid
import datetime
from flask import g
from app.main import db
from app.main.core.errors import BadRequestError
from app.main.core.auth import Auth
from app.main.core.rac import RACMgr, RACRoles
from app.main.model.user import User

def get_request_user():
    req_user = g.current_user
    user = User.query.filter_by(id=req_user['user_id']).first()
    return user
    

def save_new_user(data, desired_role: RACRoles = None):
    """ Saves a new User

        Parameters
        ----------
        data : dict
            the user data
        desired_role : RACRoles
            Optional role to assign during creation of new user
    """
    if not data.get('email'):
        raise BadRequestError('Cannot create a new User without providing an email')
    elif not data.get('username'):
        raise BadRequestError('Cannot create a new User without providing a desired username')
    elif not data.get('password'):
        raise BadRequestError('Cannot create a new User without providing a desired password')

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        new_user = User(
            public_id=str(uuid.uuid4()),
            email=data.get('email'),
            username=data.get('username'),
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            title=data.get('title'),
            language=data.get('language'),
            personal_phone=data.get('personal_phone'),
            voip_route_number=data.get('voip_route_number'),
            registered_on=datetime.datetime.utcnow()
        )

        if desired_role:
            new_user = RACMgr.assign_role_to_user(desired_role, new_user)

        save_changes(new_user)
        return generate_token(new_user)
    else:
        response_object = {
            'status': 'fail',
            'message': 'User already exists. Please Log in.',
        }
        return response_object, 409


def update_user(public_id, data):
    user = User.query.filter_by(public_id=public_id).first()
    if user:
        for attr in data:
            if hasattr(user, attr):
                setattr(user, attr, data.get(attr))

        save_changes(user)

        response_object = {
            'success': True,
            'message': 'User updated successfully',
        }
        return response_object, 200
    else:
        response_object = {
            'success': False,
            'message': 'User not found',
        }
        return response_object, 404


def get_all_users():
    return User.query.all()


def get_a_user(public_id):
    return User.query.filter_by(public_id=public_id).first()


def get_user_by_mailbox_id(employee_mailbox_id: str):
    assert employee_mailbox_id is not None

    return User.query.filter(User.pbx_mailbox_id == employee_mailbox_id).first()


def get_user_by_caller_id(caller_id: str):
    assert caller_id is not None

    return User.query.filter(User.pbx_caller_id == caller_id).first()


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()


def generate_token(user):
    try:
        auth_token = Auth.encode_auth_token(user.id)

        response_object = {
            'status': 'success',
            'message': 'Successfully registered.',
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'title': user.title,
                'token': auth_token.decode()
            }
        }
        return response_object, 201
    except Exception as e:
        response_object = {
            'status': 'fail',
            'message': 'Some error occurred. Please try again.'
        }
        return response_object, 401
