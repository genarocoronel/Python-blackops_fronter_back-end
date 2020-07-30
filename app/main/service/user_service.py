import uuid
import datetime

import phonenumbers
from flask import g
from app.main import db
from app.main.core.errors import BadRequestError
from app.main.core.auth import Auth
from app.main.core.rac import RACMgr, RACRoles
from app.main.model.candidate import Candidate
from app.main.model.client import Client
from app.main.model.pbx import PBXNumber
from app.main.model.user import User, UserClientAssignment, UserLeadAssignment, UserCandidateAssignment, UserPBXNumber
from sqlalchemy import func


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def get_request_user():
    # TODO: should modify flask context to set the 'current_user' to a User model instance
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

    # HTTP request
    if not desired_role:
        role = data.get('rac_role') 
        if not role:
            raise BadRequestError('Cannot crate a user without providing a role')
        desired_role = RACRoles(role)

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        # department
        dept = Department.from_role(desired_role.value)
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
            pbx_mailbox_id=data.get('pbx_mailbox_id'),
            department=dept,
            registered_on=datetime.datetime.utcnow()
        )

        # assign role to user  
        new_user = RACMgr.assign_role_to_user(desired_role, new_user)
        save_changes(new_user)

        if dept == Department.SALES.name:
            # Add a sales board to Sales agents
            sb = SalesBoard(agent_id=new_user.id)
            save_changes(sb)

        return new_user
    else:
        raise BadRequestError('User with email adready present in the system')

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
    """ Gets all Users """
    user_role = g.current_user['rac_role']
    if user_role not in (RACRoles.SUPER_ADMIN.value, RACRoles.ADMIN.value):
            raise ForbiddenError('You do not have permissions to this resource.')

    return User.query.all()


def get_all_users_by_rolename(rac_role_name):
    """ Gets all Users belonging to a RAC Role name """
    role = RACMgr.get_role_record_by_name(rac_role_name)
    return User.query.filter_by(role=role).all()


def get_all_users_by_role_pubid(role_pub_id):
    """ Gets all Users belonging to a RAC Role public ID """
    role = RACMgr.get_role_record_by_pubid(role_pub_id)
    return User.query.filter_by(role=role).all()


def get_a_user(public_id):
    return User.query.filter_by(public_id=public_id).first()


def get_user_by_id(id):
    return User.query.filter_by(id=id).first()


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


def get_client_assignments(current_user):
    client_assignments = UserClientAssignment.query.join(User).filter(User.id == current_user.id).all()
    return [assignment.client for assignment in client_assignments]


def get_lead_assignments(current_user):
    """ Gets all Leads assigned to the given User """
    lead_assignments = UserLeadAssignment.query.join(User).filter(User.id == current_user.id).all()
    return [assignment.client for assignment in lead_assignments]


def get_candidate_assignments(current_user):
    candidate_assignments_filter = UserCandidateAssignment.query.join(User).filter(User.id == current_user.id)
    candidate_assignments = candidate_assignments_filter.all()
    return [assignment.candidate for assignment in candidate_assignments]


def get_user_numbers(user):
    user_pbx_numbers = UserPBXNumber.query.join(User).filter(User.id == user.id).all()
    return [number.pbx_number for number in user_pbx_numbers]


def update_user_numbers(user, new_pbx_numbers=None):
    prev_pbx_numbers = UserPBXNumber.query.join(User).filter(User.id == user.id).all()

    for prev_number in prev_pbx_numbers:
        UserPBXNumber.query.filter(UserPBXNumber.user_id == user.id,
                                   UserPBXNumber.pbx_number_id == prev_number.pbx_number_id).delete()

    if new_pbx_numbers:
        pbx_numbers = PBXNumber.query.filter(
            PBXNumber.number.in_([phonenumbers.parse(number, 'US').national_number for number in new_pbx_numbers])).all()

        if len(pbx_numbers) != len(new_pbx_numbers):
            raise Exception('Invalid PBX Numbers provided')

        for pbx_number in pbx_numbers:
            new_pbx_number = UserPBXNumber(user=user, pbx_number=pbx_number)
            db.session.add(new_pbx_number)

    save_changes()

