import enum
from flask import g

from app.main import db
from app.main.model.rac import RACRole, RACPermission, RACResource
from app.main.core.errors import NotFoundError
from sqlalchemy import and_


class RACRoles(enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPENER_REP = "opener_rep"
    OPENER_MGR = "opener_mgr"
    SALES_REP = "sales_rep"
    SALES_MGR = "sales_mgr"
    SALES_ADMIN = "sales_admin"
    SERVICE_REP = "service_rep"
    SERVICE_MGR = "service_mgr"
    SERVICE_ADMIN = "service_admin"
    DOC_PROCESS_REP = "doc_process_rep"
    DOC_PROCESS_MGR = "doc_process_mgr"

    @classmethod
    def is_valid_role(cls, role):
        roles = set(item.value for item in cls)
        return role in roles

    @classmethod
    def from_str(cls, value):
        return next((e for e in cls if e.value == value), None)


class RACMgr():
    """ Represents the Role Access Control Manager """

    @classmethod
    def does_policy_deny(cls, resource):
        """ Checks if there's a Deny policy in place for RAC resource """
        # Allways allow Super Admin
        if (g.current_user['rac_role'] == RACRoles.SUPER_ADMIN.value 
                or g.current_user['rac_role'] == RACRoles.ADMIN.value):
            return False
        else:
            role_policy = cls.get_policy_for_role(g.current_user["rac_role"])
            # Always deny if a Role does not have a policy.
            if not role_policy:
                return True
            else:
                return resource in role_policy['deny']

    @classmethod
    def does_same_user_policy_deny(cls, target_user_id):
        """ Denies if not same user but allows for Admins """
        if (g.current_user['rac_role'] == RACRoles.SUPER_ADMIN.value 
                or g.current_user['rac_role'] == RACRoles.ADMIN.value):
            return False
        elif g.current_user['public_id'] == target_user_id:
            return False
        else:
            return True
    
    @classmethod
    def enforce_policy_user_has_role(cls, roles_to_enforce):
        """ Allows if user has one of the Roles specified """
        if not hasattr(g, 'current_user') or 'rac_role' not in g.current_user:
            raise Exception("Unauthorized user")

        # if no roles specified - ALLOW ALL
        if not roles_to_enforce:
            return True

        """ Always allow for admins """
        if (g.current_user['rac_role'] == RACRoles.SUPER_ADMIN.value
            or g.current_user['rac_role'] == RACRoles.ADMIN.value):
            return True

        for role_item in roles_to_enforce:
            if not RACRoles.is_valid_role(role_item.value):
                raise Exception('A given role to enforce is not a known type')

            if g.current_user['rac_role'] == role_item.value:
                return True

        return False

    @classmethod
    def does_user_has_permission(cls, resource_name):
        if not hasattr(g, 'current_user') or 'rac_role' not in g.current_user:
            raise Exception("Unauthorized user")
        # check permission in db
        perm = RACPermission.query.outerjoin(RACRole, RACResource)\
                                  .filter(and_(RACRole.name==g.current_user['rac_role'], RACResource.name==resource_name)).first()
        if perm:
            return True
        return False

    @classmethod
    def get_policy_for_role(cls, role):
        policy = None

        if RACRoles.is_valid_role(role):
            policies = cls.get_access_policies()
            for policy_item in policies:
                if policy_item['rac_role'] == role:
                    policy = policy_item
        
        return policy

    @classmethod
    def get_access_policies(cls):
        # TODO: Move this to data system and models
        policies = [
            {
                'rac_role': RACRoles.SUPER_ADMIN.value,
                'deny': [],
                'allow': ["*"]
            },
            {
                'rac_role': RACRoles.ADMIN.value,
                'deny': ['admins.create'],
                'allow': []
            },
            {
                'rac_role': RACRoles.SERVICE_REP.value,
                'deny': ['users.list', 'users.create', 'admins.*'],
                'allow': []
            },
            {
                'rac_role': RACRoles.SERVICE_MGR.value,
                'deny': ['admins.*'],
                'allow': []
            },
            {
                'rac_role': RACRoles.SALES_REP.value,
                'deny': ['users.list', 'users.create', 'admins.*'],
                'allow': []
            },
            {
                'rac_role': RACRoles.SALES_MGR.value,
                'deny': ['admins.*'],
                'allow': []
            },
            {
                'rac_role': RACRoles.OPENER_REP.value,
                'deny': ['users.list', 'users.create', 'admins.*'],
                'allow': []
            },
            {
                'rac_role': RACRoles.DOC_PROCESS_MGR.value,
                'deny': ['admin.*'],
                'allow': []
            },
            {
                'rac_role': RACRoles.DOC_PROCESS_REP.value,
                'deny': ['users.list', 'users.create', 'admins.*'],
                'allow': []
            }
        ]
        return policies

    @classmethod
    def get_all_roles(cls):
        roles = []
        role_records = cls._handle_get_roles()
        if not role_records:
            raise NotFoundError('Could not find any RAC Roles!')

        if role_records:
            for role_record_item in role_records:
                role = {
                    'id': role_record_item.public_id,
                    'name': role_record_item.name,
                    'name_friendly': role_record_item.name_friendly,
                    'description': role_record_item.description,
                    'inserted_on': role_record_item.inserted_on,
                    'updated_on': role_record_item.updated_on
                }
                roles.append(role)

        return roles

    @classmethod
    def get_role_by_name(cls, role_name):
        role_record = cls._handle_get_role_by_name(role_name)
        if role_record:
            return {
                'id': role_record.public_id,
                'name': role_record.name,
                'name_friendly': role_record.name_friendly,
                'description': role_record.description,
                'inserted_on': role_record.inserted_on,
                'updated_on': role_record.updated_on
            }
        else:
            raise NotFoundError(f'That role {role} does not exist')

    @classmethod
    def get_role_record_by_name(cls, role_name):
        return cls._handle_get_role_by_name(role_name)

    @classmethod
    def get_role_by_pubid(cls, pub_id):
        role_record = cls._handle_get_role_by_pubid(pub_id)
        if role_record:
            return {
                'id': role_record.public_id,
                'name': role_record.name,
                'name_friendly': role_record.name_friendly,
                'description': role_record.description,
                'inserted_on': role_record.inserted_on,
                'updated_on': role_record.updated_on
            }
        else:
            raise NotFoundError(f'That role {role} does not exist')

    @classmethod
    def get_role_record_by_pubid(cls, pub_id):
        return cls._handle_get_role_by_pubid(pub_id)
    
    @classmethod
    def assign_role_to_user(cls, desired_role, user):
        # TODO: enforce policy on who can assign role to user (watch for Admin)
        desired_role_record = cls._handle_get_role_by_name(desired_role.value)
        user.role = desired_role_record
        return user

    @classmethod
    def _handle_get_roles(cls):
        return RACRole.query.all()

    @classmethod
    def _handle_get_role_by_name(cls, role_name):
        return RACRole.query.filter_by(name=role_name).first()

    @classmethod
    def _handle_get_role_by_pubid(cls, pub_id):
        return RACRole.query.filter_by(public_id=pub_id).first()
