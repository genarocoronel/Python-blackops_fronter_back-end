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
from app.main.model.user import User, UserClientAssignment, UserLeadAssignment, UserCandidateAssignment, UserPBXNumber, Department
from app.main.model.sales_board import SalesBoard
from sqlalchemy import func


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def get_request_user():
    # TODO: should modify flask context to set the 'current_user' to a User model instance
    user = None
    
    if 'current_user' in g:
        req_user = g.current_user if g.current_user else None
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
    # HTTP request
    if desired_role:
        rac_role = RACMgr.get_role_record_by_name(desired_role.value)
    else:
        rac_role = RACMgr.get_role_record_by_pubid(data.get('rac_role_id'))

    if not rac_role:
        raise Exception('Could not find that role by its ID {}'.format(data.get('rac_role_id')))

    user = User.query.filter_by(email=data['email']).first()
    if not user:
        # department
        dept = Department.from_role(rac_role.name)
        
        new_user = User(
            public_id=str(uuid.uuid4()),
            email=data.get('email'),
            username=data.get('username'),
            password=data.get('password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            language=data.get('language') if 'language' in data else 'en',
            personal_phone=data.get('personal_phone'),
            voip_route_number=data.get('voip_route_number') if 'voip_route_number' in data else None,
            pbx_mailbox_id=data.get('pbx_mailbox_id') if 'pbx_mailbox_id' in data else None,
            department=dept,
            registered_on=datetime.datetime.utcnow()
        )

        # assign role to user  
        new_user = RACMgr.assign_role_to_user(rac_role, new_user)
        save_changes(new_user)

        if dept == Department.SALES.name:
            # Add a sales board to Sales agents
            sb = SalesBoard(agent_id=new_user.id)
            save_changes(sb)

        return new_user
    else:
        raise BadRequestError('User with email already present in the system')

def update_user(public_id, data):
    user = User.query.filter_by(public_id=public_id).first()
    if user:
        for attr in data:
            if attr == 'rac_role_id':
                desired_role = RACMgr.get_role_record_by_pubid(data.get('rac_role_id'))
                
                if not desired_role:
                    raise Exception('Could not find that role by its ID {}'.format(data.get('rac_role_id')))
                
                dept = Department.from_role(desired_role.name)
                user.department = Department.from_role(desired_role.name)
                user = RACMgr.assign_role_to_user(desired_role, user)
            
            if attr == 'password':
                setattr(user, attr, data.get(attr))
            
            elif hasattr(user, attr):
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


def get_assignment_for_candidate(candidate):
    candidate_assignment = UserCandidateAssignment.query.join(User).filter(Candidate.id == candidate.id).first()
    return candidate_assignment


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


def get_department_users(name):
    users = User.query.filter(func.lower(User.department) == func.lower(name)).all()
    return users 

