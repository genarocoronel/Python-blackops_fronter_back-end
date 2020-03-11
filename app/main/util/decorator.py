from functools import wraps
from flask import request, g

from app.main.core.auth import Auth
from ..util.dto import AuthDto
from ..core.rac import RACMgr

api = AuthDto.api


# TODO: Enhance to accept more granular actions on resources and sub-resources
def enforce_rac_policy(rac_resource):
    """ Decorator to enforce Role Access Control """
    def decorator(func_to_decorate):
        @wraps(func_to_decorate)
        def decorated(*orig_args, **orig_kwargs):
            if RACMgr.does_policy_deny(rac_resource):
                api.abort(403, 'You do not have permissions to access this resource or action', success=False)

            return func_to_decorate(*orig_args, **orig_kwargs)

        return decorated
    return decorator


def enforce_rac_same_user_policy(func_to_decorate):
    @wraps(func_to_decorate)
    def decorated(*orig_args, **orig_kwargs):
        if 'user_id' in orig_kwargs and RACMgr.does_same_user_policy_deny(orig_kwargs.get('user_id')):
            api.abort(403, 'You do not have permissions to access this resource or action', success=False)

        return func_to_decorate(*orig_args, **orig_kwargs)

    return decorated
        

def token_required(f):
    """ Decorator to enforce Authenticated session """
    @wraps(f)
    def decorated(*args, **kwargs):
        data, status = Auth.get_logged_in_user(request)
        curr_user = data.get('data')

        if not curr_user:
            api.abort(status, data.get('message'))

        g.current_user = curr_user
        return f(*args, **kwargs)

    return decorated
