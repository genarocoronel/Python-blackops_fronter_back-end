import uuid
import datetime
import re
from twilio.rest import Client
from flask import current_app

from app.main import db
from app.main.model.sms import SMSConvo, SMSMessage, SMSMediaFile, SMSBandwidth
from app.main.model.client import Client, ClientContactNumber
from app.main.model.contact_number import ContactNumber
from app.main.service.client_service import get_client_by_phone, get_client_by_id, get_client_by_public_id

account_sid = "AC27a28affdf746d9c7b06788016b35c8c"
sms_auth_token = "a91db8822f78e7a928676140995290db"

PROVIDER_BANDWIDTH = 'bandwidth'
PROVIDER_JIVE = 'jive'


def whois_webhook_token(webhook_token):
    """ Checks if a Webhook token for SMS message registration is valid """
    provider_name = None
    
    for whtoken, provider in current_app.sms_webhook_identities.items():
        if webhook_token == whtoken:
            provider_name = provider
            break

    return provider_name


def get_convo(convo_public_id):
    """ Gets a SMS Conversation """
    convo_with_mssgs = None
    convo = _get_sms_convo_by_pubid(convo_public_id)
    if convo:
        convo_with_mssgs = synth_messages_for_convo(convo)
    
    return convo_with_mssgs


def get_convo_for_client(client_public_id):
    """ Gets a SMS Conversation for a given Client """
    convo_with_mssgs = None
    client = get_client_by_public_id(client_public_id)  
    if client:
        convo = _get_sms_convo_by_client_id(client.id)
        if convo:   
            convo_with_mssgs = synth_messages_for_convo(convo, client)
    
    return convo_with_mssgs


def synth_messages_for_convo(convo, client=None):
    convo_with_mssgs = None

    if convo:
        if not client:
            client = get_client_by_id(convo.client_id)       

        convo_with_mssgs = {
            'public_id': convo.public_id,
            'client_public_id':client.public_id,
            'items':[]
        }

        messages = SMSMessage.query.filter_by(sms_convo_id=convo.id).order_by(db.desc(SMSMessage.id)).all()
        for mssg_item in messages:
            tmp_mssg = {
                'public_id': mssg_item.public_id,
                'from_phone': mssg_item.from_phone,
                'to_phone': mssg_item.to_phone,
                'network_time': mssg_item.network_time,
                'direction': mssg_item.direction,
                'segment_count': mssg_item.segment_count,
                'body_text': mssg_item.body_text,
                'message_media': [],
                'provider_message_id': mssg_item.provider_message_id,
                'provider_name': mssg_item.provider_name,
                'is_viewed': mssg_item.is_viewed
            }

            tmp_media_records = _handle_get_media_for_messg(mssg_item)
            if tmp_media_records:
                for media_item in tmp_media_records:
                    tmp_media = {
                        'public_id': media_item.public_id,
                        'file_uri': media_item.file_uri
                    }
                    tmp_mssg['message_media'].append(tmp_media)

            convo_with_mssgs['items'].append(tmp_mssg)
    
    return convo_with_mssgs


def register_new_sms_mssg(mssg_data, provider_name):
    """ Registers a new SMS message and tries to associate it with a Conversation """
    result = None
    if (provider_name == PROVIDER_BANDWIDTH):
        crm_mssg_data = _save_bandwidth_sms_message(mssg_data)
        crm_mssg = process_new_sms_mssg(crm_mssg_data)

        result = {
                'success': True,
                'message': "Successfully registered a Provider SMS message. Thank you.",
                'our_message_id': crm_mssg.public_id
            }
    else:
        raise Exception(f'Error: That SMS provider {provider_name} is unknown.')
    
    return result


def process_new_sms_mssg(mssg_data):
    """ Processes a new CRM SMS message """
    message_public_id = None
    from_phone = None
    
    sms_mssg = SMSMessage.query.filter_by(provider_message_id=mssg_data['provider_message_id']).first()
    if not sms_mssg:
        mssg_data['from_phone'] = clean_phone_to_tenchars(mssg_data['from_phone'])
        mssg_data['to_phone'] = clean_phone_to_tenchars(mssg_data['to_phone'])

        if mssg_data['from_phone'] is None:
            raise Exception('Error: The FROM phone is None!')
        elif len(mssg_data['from_phone']) < 10:
            raise Exception('Error: The FROM phone number has less than 10 characters!')
        
        # TODO: Later add unmatched, incoming phone numbers to be "sent to a general convo"
        client = get_client_by_phone(mssg_data['from_phone'])

        client_conversation = _get_sms_convo_by_client(client)
        if not client_conversation:
            client_conversation = _handle_new_sms_conversation(client)

        sms_mssg = _handle_new_sms_message(mssg_data, client_conversation)
        if not sms_mssg:
            raise Exception('Error: could not create a SMS message for a conversation!')

    return sms_mssg


def sms_send_raw(phone_target, sms_text, user_id):

    client = Client(account_sid, sms_auth_token)
    new_sms_message = SMSMessage(user_id=user_id, text=sms_text, phone_target=phone_target, status='created')

    try:
        message = client.messages.create(
            to=phone_target,
            from_="+18584139754",
            body=sms_text)
        new_sms_message.message_provider_id = message.sid
        new_sms_message.status = 'sent'
    except Exception as e:
        new_sms_message.status = 'failed_to_send'
    finally:
        db.session.add(new_sms_message)
        db.session.commit()


def clean_phone_to_tenchars(raw_phone):
    return re.sub('[^0-9]','',raw_phone.strip())[1:]


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()


def _handle_new_sms_conversation(client):
    """ Saves a new Client SMS Conversation """
    new_convo = SMSConvo(
        public_id = str(uuid.uuid4()),
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow()
    )
    db.session.add(new_convo)
    save_changes()

    return new_convo


def _handle_new_sms_message(message_data, conversation):
    """ Saves SMS Message for a Conversation """
    new_message = SMSMessage(
        public_id = str(uuid.uuid4()),
        from_phone = message_data['from_phone'],
        to_phone = message_data['to_phone'],
        network_time = message_data['network_time'],
        direction = message_data['direction'],
        segment_count = message_data['segment_count'],
        body_text = message_data['body_text'],
        provider_message_id = message_data['provider_message_id'],
        provider_name = message_data['provider_name'],
        is_viewed = False,
        sms_convo_id = conversation.id,
        inserted_on = datetime.datetime.utcnow(),
    )
    db.session.add(new_message)
    save_changes()

    if new_message and message_data['message_media']:
        media_records = _handle_new_media(message_data['message_media'], new_message)

    return new_message


def _handle_new_media(media_data, message):
    """ Saves Media (MMS) for given SMS Message """
    media_records = []    
    if message and media_data and isinstance(media_data, list):
        for media_item in media_data:
            tmp_media_item = SMSMediaFile(
                public_id = str(uuid.uuid4()),
                file_uri = media_item,
                inserted_on = datetime.datetime.utcnow(),
                sms_message_id = message.id
            )
            db.session.add(tmp_media_item)
            save_changes()
            media_records.append(tmp_media_item)

    return media_records


def _get_sms_convo_by_client(client):
    return SMSConvo.query.filter(SMSConvo.client_id == client.id).first()


def _get_sms_convo_by_pubid(public_id):
    return SMSConvo.query.filter(SMSConvo.public_id == public_id).first()


def _get_sms_convo_by_client_id(client_id):
    return SMSConvo.query.filter(SMSConvo.client_id == client_id).first()


def _handle_get_bandwidth_message(bandwidth_message_id):
    return SMSBandwidth.query.filter_by(message_id=bandwidth_message_id).first()


def _save_bandwidth_sms_message(messg_data):
    """ Saves a Bandwidth SMS/MMS message """
    bw_mssg = _handle_get_bandwidth_message(messg_data['message']['id'])
    message_media = None

    if not bw_mssg:
        if messg_data['message']['media']:
            message_media = messg_data['message']['media']

        bw_mssg=SMSBandwidth(
            time=messg_data['time'],
            type=messg_data['type'],
            to=messg_data['to'],
            description=messg_data['description'],
            message_id=messg_data['message']['id'],
            message_owner=messg_data['message']['owner'],
            message_application_id=messg_data['message']['applicationId'],
            message_time=messg_data['message']['time'],
            message_segment_count=messg_data['message']['segmentCount'],
            message_direction=messg_data['message']['direction'],
            message_to=messg_data['message']['to'],
            message_from=messg_data['message']['from'],
            message_text=messg_data['message']['text'],
            message_media=message_media,
            inserted_on=datetime.datetime.utcnow(),
        )

        db.session.add(bw_mssg)
        save_changes()

    crm_mssg_data = {
        'from_phone':bw_mssg.message_from,
        'to_phone':bw_mssg.message_to,
        'network_time':bw_mssg.time,
        'direction':bw_mssg.message_direction,
        'segment_count':bw_mssg.message_segment_count,
        'body_text':bw_mssg.message_text,
        'message_media':message_media,
        'provider_message_id':bw_mssg.message_id,
        'provider_name':'bw'
    }

    return crm_mssg_data


def _handle_get_media_for_messg(message):
    return SMSMediaFile.query.filter_by(sms_message_id=message.id).order_by(db.desc(SMSMediaFile.id)).all()
