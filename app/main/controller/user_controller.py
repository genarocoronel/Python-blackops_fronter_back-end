from flask import request
from flask_restplus import Resource

from ..core.errors import BadRequestError
from ..util.decorator import (token_required, enforce_rac_policy, 
        enforce_rac_same_user_policy, enforce_rac_required_roles)
from ..util.dto import UserDto, TaskDto
from ..core.auth import Auth
from ..core.rac import RACRoles
from ..service.user_service import (save_new_user, get_all_users, get_a_user, 
    update_user, get_all_users_by_role_pubid)
from ..service.user_service import DepartmentService
from ..service.usertask_service import UserTaskService

api = UserDto.api
_user = UserDto.user
_user_supressed = UserDto.user_supressed
_new_user = UserDto.new_user
_update_user = UserDto.update_user
_task = TaskDto.user_task


@api.route('')
class UserList(Resource):
    @api.response(201, 'User successfully created.')
    @api.doc('create a new user')
    @api.expect(_new_user, validate=True)
    @token_required
    @enforce_rac_required_roles([RACRoles.SUPER_ADMIN, RACRoles.ADMIN])
    def post(self):
        """Creates a new User """
        data = request.json
        try:
            new_user_response = save_new_user(data=data, desired_role = data.get('rac_role'))
            response_object = {
                'success': True,
                'data': new_user_response
            }
            return response_object, 200
        except BadRequestError as e:
            api.abort(400, message='Error creating new user, {}'.format(str(e)), success=False)
        except Exception as e:
            api.abort(500, message=f'Failed to create new user. Please report this issue.', success=False)

        return new_user_response

    @api.doc('List all registered users')
    @api.marshal_list_with(_user, envelope='data')
    @token_required
    @enforce_rac_policy(rac_resource='users.list')
    def get(self):
        """List all registered users"""
        users = []

        user_records = get_all_users()
        for user_record_item in user_records:
            tmp_user = {
                'public_id': user_record_item.public_id,
                'username': user_record_item.username,
                'password': None,
                'email': user_record_item.email,
                'first_name': user_record_item.first_name,
                'last_name': user_record_item.last_name,
                'title': user_record_item.title,
                'language': user_record_item.language,
                'phone_number': user_record_item.personal_phone,
                'personal_phone': user_record_item.personal_phone,
                'last_4_of_phone': user_record_item.personal_phone[-4:],
                'voip_route_number': user_record_item.voip_route_number,
                'rac_role': user_record_item.role.name
            }
            users.append(tmp_user)

        return users

@api.route('/members/<role_pub_id>')
@api.param('role_pub_id', 'RAC Role public ID')
class UsersRoleMembers(Resource):
    @api.doc('Get users that are members of a RAC Role')
    @api.marshal_with(_user_supressed, envelope='data')
    @token_required
    def get(self, role_pub_id):
        """ Get all users (supressed) by RAC role membership """
        users = []

        user_records = get_all_users_by_role_pubid(role_pub_id)
        for user_record_item in user_records:
            tmp_user = {
                'public_id': user_record_item.public_id,
                'username': user_record_item.username,
                'first_name': user_record_item.first_name,
                'last_name': user_record_item.last_name,
                'language': user_record_item.language,
                'voip_route_number': user_record_item.voip_route_number,
                'rac_role': user_record_item.role.name
            }
            users.append(tmp_user)

        return users

@api.route('/<user_id>')
@api.param('user_id', 'The User public identifier')
@api.response(404, 'User not found.')
class UpdateUser(Resource):
    @api.doc('get a user')
    @api.marshal_with(_user)
    @token_required
    def get(self, user_id):
        """get a user given its identifier"""
        user_record = get_a_user(user_id)
        if not user_record:
            api.abort(404, f'Could not find a User with ID {user_id}')
        
        user = {
            'public_id': user_record.public_id,
            'username': user_record.username,
            'password': None,
            'email': user_record.email,
            'first_name': user_record.first_name,
            'last_name': user_record.last_name,
            'title': user_record.title,
            'language': user_record.language,
            'phone_number': user_record.personal_phone,
            'personal_phone': user_record.personal_phone,
            'last_4_of_phone': user_record.personal_phone[-4:],
            'voip_route_number': user_record.voip_route_number,
            'rac_role': user_record.role.name
        }
        return user
    
    @api.doc('update user')
    @api.expect(_update_user, validate=True)
    @token_required
    @enforce_rac_same_user_policy
    def put(self, user_id):
        """Update User Account"""
        return update_user(user_id, request.json)

@api.route('/<dept_name>/members')
@api.param('dept_name', 'Department name')
class UsersByDept(Resource):

    #@token_required
    @api.marshal_list_with(_user_supressed) 
    def get(self, dept_name):
        try:
            dept = DepartmentService.by_name(dept_name)
            return dept.members()
        except Exception as err:
            api.abort(500, "{}".format(str(err)))

@api.route('/<user_id>/tasks')
@api.param('user_id', 'User Identifier')
class UserTasks(Resource):

    @token_required
    @api.marshal_list_with(_task)
    def get(self, user_id): 
        try:
            if 'all' in user_id:
                service = UserTaskService.request() 
            else:
                service = UserTaskService.request_user(user_id)
            return service.list()

        except Exception as err:
            api.abort(500, "{}".format(str(err)))

