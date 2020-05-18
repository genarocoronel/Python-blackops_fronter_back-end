import uuid
import datetime
from app.main import db
from app.main.core.errors import BadRequestError
from app.main.core.auth import Auth
from app.main.core.helper import generate_rand_code, generate_hash_sha512
from app.main.model.portal_user import PortalUser


def get_portal_user_by_id(id):
    return PortalUser.query.filter_by(id=id).first()


def get_portal_user_by_pubid(public_id):
    return PortalUser.query.filter_by(public_id=id).first()


def get_portal_user_by_email(email):
    return PortalUser.query.filter_by(email=email).first()

def get_portal_user_by_invite(invite_token):
    return PortalUser.query.filter_by(invite_token=invite_token).first()


def create_portal_user(email, username, client_id, password=None, is_disabled=False):
    if get_portal_user_by_email(email):
        raise NoDuplicateAllowed('A Portal User with that email already exists.')
    else:
        # Used for initial password and also saving in challenge 2fa to help
        # the customer if they need assistance on first-time logging in 
        challenge_2fa = generate_rand_code()
        user = PortalUser(
            public_id = str(uuid.uuid4()),
            email = email,
            username = username,
            password = challenge_2fa,
            challenge_2fa = challenge_2fa,
            client_id = client_id,
            is_disabled = is_disabled,
            invite_token = generate_hash_sha512(),
            registered_on = datetime.datetime.utcnow()
        )
        _save_changes(user)

    return user


def reset_challenge_2fa(user_id):
    """ Resets a 2FA challenge code for a Portal User """
    challenge_code = None
    puser = get_portal_user_by_id(user_id)
    if puser:
        challenge_code = generate_rand_code()
        puser.challenge_2fa = challenge_code
        _save_changes(puser)

    return challenge_code


def is_challenge_2fa_valid(challenge_code):
    """ Checks whether a 2FA code is Valid for a Portal User """
    is_valid = False
    user = PortalUser.query.filter_by(challenge_2fa=challenge_code).first()
    if user:
        is_valid = True

    return is_valid


def invite_redeem(desired_password, invite_token):
    """ Redeems a Invite to claim Portal account """
    is_redeem_success = False
    puser = get_portal_user_by_invite(invite_token)
    if puser:
        puser.password = desired_password
        puser.invite_token = None
        puser.is_claimed = True
        puser.challenge_2fa = None
        _save_changes(puser)
        is_redeem_success = True

    return is_redeem_success

def reset_invite(user_id):
    """ Resets the invite hash for a Portal User """
    invite_token = None
    puser = get_portal_user_by_id(user_id)
    if puser:
        invite_token = generate_hash_sha512()
        puser.invite_token = invite_token
        _save_changes(puser)

    return invite_token


def is_invite_valid(invite_token):
    """ Checks whether a Invite code is Valid for a Portal User """
    is_valid = False
    user = PortalUser.query.filter_by(invite_token=invite_token).first()
    if user:
        is_valid = True

    return is_valid


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()