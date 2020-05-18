import uuid
import datetime
from flask import g

from app.main import db
from app.main.core.errors import BadRequestError
from app.main.model.portal_message import PortalMessage, PortalMssgDirection
from app.main.service.portal_user_service import get_portal_user_by_pubid, get_portal_user_by_id
from app.main.service.client_service import get_client_by_id
from app.main.service.user_service import get_user_by_id


def get_messages_for_portal_user():
    mssgs = []
    puser = get_portal_user_by_pubid(g.current_portal_user['public_id'])
    if puser:
        mssg_records = PortalMessage.query.filter_by(portal_user_id=puser.id).all()

        if mssg_records:
            for mssg_item in mssg_records:
                tmp_mssg = synth_message(mssg_item)
                mssgs.append(tmp_mssg)

    return mssgs


def create_inbound_message(content):
    mssg_response = None
    puser = get_portal_user_by_pubid(g.current_portal_user['public_id'])
    client = get_client_by_id(puser.client_id)

    if puser:
        mssg = PortalMessage(
            public_id = str(uuid.uuid4()),
            portal_user_id = puser.id,
            content = content,
            direction = PortalMssgDirection.INBOUND.value,
            author_id = puser.id,
            author_name = '{} {}'.format(client.first_name, client.last_name),
            inserted_on = datetime.datetime.utcnow(),
        )
        _save_changes(mssg)

        mssg_response = synth_message(mssg)

    return mssg_response


def synth_message(message):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    puser = get_portal_user_by_id(message.portal_user_id)
    author = puser
    if (message.direction == PortalMssgDirection.OUTBOUND.value):
        author = get_user_by_id(message.author_id)
    
    mssg_synth = {
        'public_id': message.public_id,
        'portal_user_public_id': puser.public_id,
        'content': message.content,
        'direction': message.direction,
        'author_public_id': author.public_id,
        'author_name': message.author_name,
        'is_viewed': message.is_viewed,
        'inserted_on': message.inserted_on.strftime(datetime_format)
    }

    return mssg_synth


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()