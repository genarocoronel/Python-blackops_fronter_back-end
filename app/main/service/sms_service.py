import uuid
import datetime
import re
import enum
from twilio.rest import Client as Twilio_Client

from app.main import db
from app.main.model.sms import SMSConvo, SMSMessage, SMSMediaFile, SMSBandwidth, SMSMessageStatus
from app.main.model.client import Client, ClientContactNumber
from app.main.model.contact_number import ContactNumber
from app.main.service.client_service import get_client_by_phone, get_client_by_id, get_client_by_public_id
from app.main.service.third_party.bandwidth_service import sms_send
from app.main.core.errors import BadRequestError, NotFoundError, ConfigurationError, ServiceProviderError
from flask import current_app


account_sid = "AC27a28affdf746d9c7b06788016b35c8c"
sms_auth_token = "a91db8822f78e7a928676140995290db"

PROVIDER_BANDWIDTH = 'bandwidth'
PROVIDER_JIVE = 'jive'


class MessageDirection(enum.Enum):
    IN = "in"
    OUT = "out"


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
    current_app.logger.info(f'Fetching the client SMS conversation with ID {convo_public_id}')
    convo = _get_sms_convo_by_pubid(convo_public_id)
    if not convo:
        raise NotFoundError(f"Conversation for  with ID {convo_public_id} not found.")
        
    convo_with_mssgs = synth_messages_for_convo(convo)
    if not convo_with_mssgs:
        raise NotFoundError(f"Messages for conversation with ID {convo_public_id} not found.")
    
    return convo_with_mssgs


def get_convo_for_client(client_public_id):
    """ Gets a SMS Conversation for a given Client """
    convo_with_mssgs = None
    client = get_client_by_public_id(client_public_id)  
    if not client:
        raise NotFoundError(f"Client with ID {client_public_id} not found.")
        
    convo = _get_sms_convo_by_client_id(client.id)
    if not convo:
        raise NotFoundError(f"Conversation for client with ID {client_public_id} not found.")
        
    convo_with_mssgs = synth_messages_for_convo(convo, client)
    if not convo_with_mssgs:
        raise NotFoundError(f"Messages for conversation with ID {convo.public_id} not found.")
    
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
        current_app.logger.info('Synthesizing SMS conversation with all inbound and outbound messages for this client.')
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
                'is_viewed': mssg_item.is_viewed,
                'delivery_status': mssg_item.delivery_status
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
        if crm_mssg_data['direction'] == 'in':
            current_app.logger.info('Registering inbound SMS message with success delivery status.')
            crm_mssg_data['delivery_status'] = SMSMessageStatus.SUCCESS.value
            crm_mssg = process_new_sms_mssg(crm_mssg_data, MessageDirection.IN)
            
        else:
            # This case means that CRM already sent a message and saved with status PENDING and 
            # now it is being confirmed as DELIVERED or FAILED. We need to update existing message.
            crm_mssg = SMSMessage.query.filter_by(provider_message_id=mssg_data['message']['id']).first()
            if not crm_mssg_data:
                raise Exception('Could not find a matching internal message for that outbound registration with provider ID {}.'.format(mssg_data['provider_message_id']))

            if mssg_data['description'] == 'ok':
                current_app.logger.info('Registering outbound SMS message with success delivery status.')
                crm_mssg.delivery_status = SMSMessageStatus.SUCCESS.value
                crm_mssg.updated_on = datetime.datetime.utcnow()
                save_changes(crm_mssg)

            else:
                current_app.logger.warning('WARNING: Webhook registered outbound SMS as Failed. User may need to resend.')
                crm_mssg.delivery_status = SMSMessageStatus.FAILED.value
                crm_mssg.updated_on = datetime.datetime.utcnow()
                save_changes(crm_mssg)

        result = {
                'success': True,
                'message': "Successfully registered a Provider SMS message. Thank you.",
                'our_message_id': crm_mssg.public_id
            }

    else:
        raise Exception(f'That SMS provider {provider_name} is unknown.')
    
    return result


def process_new_sms_mssg(mssg_data, direction: MessageDirection):
    """ Processes a new CRM SMS message """
    message_public_id = None
    from_phone = None
    
    current_app.logger.info("Processing new SMS message and will attempt to attach to a Client SMS conversation")
    sms_mssg = SMSMessage.query.filter_by(provider_message_id=mssg_data['provider_message_id']).first()
    if not sms_mssg:
        mssg_data['from_phone'] = clean_phone_to_tenchars(mssg_data['from_phone'])
        mssg_data['to_phone'] = clean_phone_to_tenchars(mssg_data['to_phone'])

        if mssg_data['from_phone'] is None:
            raise BadRequestError('The FROM phone is None!')
        elif len(mssg_data['from_phone']) < 10:
            raise BadRequestError(f'The FROM phone number has less than 10 characters {mssg_data["from_phone"]}!')
        
        # TODO: Later add unmatched, incoming phone numbers to be "sent to a general convo"
        client = None
        if direction == MessageDirection.IN:
            client = get_client_by_phone(mssg_data['from_phone'])
        elif direction == MessageDirection.OUT:
            client = get_client_by_phone(mssg_data['to_phone'])

        if not client:
            raise Exception('Could not find a Client by phone number when attempting to process SMS message and convo')
        
        client_conversation = _get_sms_convo_by_client(client)
        if not client_conversation:
            client_conversation = _handle_new_sms_conversation(client)

        sms_mssg = _handle_new_sms_message(mssg_data, client_conversation)
        if not sms_mssg:
            raise Exception('Could not create a SMS message for a conversation!')

    return sms_mssg


def sms_send_raw(phone_target, sms_text, user_id):
    return None
    # TODO: Implement sending Twilio messages to CRM users at a later time (per Keith & David on 2020-02-28)
    # client = Twilio_Client(account_sid, sms_auth_token)
    # new_sms_message = SMSMessage(user_id=user_id, text=sms_text, phone_target=phone_target, status='created')

    # try:
    #     message = client.messages.create(
    #         to=phone_target,
    #         from_="+18584139754",
    #         body=sms_text)
    #     new_sms_message.message_provider_id = message.sid
    #     new_sms_message.status = 'sent'
    # except Exception as e:
    #     new_sms_message.status = 'failed_to_send'
    # finally:
    #     db.session.add(new_sms_message)
    #     db.session.commit()


def send_message_to_client(client_public_id, from_phone, message_body, to_phone = None):
    """ Sends a SMS message to a client on behalf of a Sales or Service person """
    current_app.logger.info(f'Attempting to send SMS message to {to_phone} frm {from_phone}.')
    sms_message = None
    destination_phone = None

    if to_phone:
        # Ensure phone belongs to client when given
        client = get_client_by_phone(clean_phone_to_tenchars(to_phone))
        if not client or client.public_id != client_public_id:
            raise BadRequestError('Client ID To phone number mismatch. Not sent.')

        destination_phone = to_phone
    else:
        client = get_client_by_public_id(client_public_id)
        if not client:
            raise NotFoundError('could not find a known Client for that outbound SMS message. Not sent.')
        
        for number_item in client.contact_numbers:
            print(number_item.contact_number)
            if number_item.contact_number.preferred:
                destination_phone = number_item.contact_number.phone_number
                break
    
    if not destination_phone:
        raise Exception(f'Could not determine phone number to send the SMS message to for Client with ID {client_public_id}')
    
    try:
        crm_mssg_data = sms_send(from_phone, destination_phone, message_body)
    except ConfigurationError as e:
        current_current_app.logger.error('Bandwidth configuration Error: {}'.format(str(e)))
        raise
    except ServiceProviderError as e:
        current_current_app.logger.error('Bandwidth remote service Error: {}'.format(str(e)))
        raise

    if crm_mssg_data:
        current_app.logger.info('Send SMS message carried out. Marking as PENDING status until webhook confirms success or failure.')
        crm_mssg_data['delivery_status'] = SMSMessageStatus.PENDING.value
        crm_mssg = process_new_sms_mssg(crm_mssg_data, MessageDirection.OUT)
        sms_message = {
            'public_id': crm_mssg.public_id,
            'from_phone': crm_mssg.from_phone,
            'to_phone': crm_mssg.to_phone,
            'network_time': crm_mssg.network_time,
            'direction': crm_mssg.direction,
            'segment_count': crm_mssg.segment_count,
            'body_text': crm_mssg.body_text,
            'message_media': [],
            'provider_message_id': crm_mssg.provider_message_id,
            'provider_name': crm_mssg.provider_name,
            'is_viewed': crm_mssg.is_viewed,
            'delivery_status': crm_mssg.delivery_status
        }

    return sms_message


def clean_phone_to_tenchars(raw_phone):
    raw_phone = re.sub('[^0-9]','',raw_phone)
    raw_phone = raw_phone.strip()
    return raw_phone[-10:]


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
    is_viewed = False
    if message_data['direction'] == MessageDirection.OUT:
        is_viewed = True

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
        is_viewed = is_viewed,
        sms_convo_id = conversation.id,
        inserted_on = datetime.datetime.utcnow(),
        delivery_status = message_data['delivery_status']
    )
    db.session.add(new_message)
    save_changes()

    if new_message and message_data['message_media'] and message_data['message_media'] != None:
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
