import base64
import requests
import json
import os

from app.main.config import upload_location
from app.main.core.errors import ConfigurationError, ServiceProviderError
from flask import current_app


def sms_send(from_phone, to_phone, message_body):
    """ Sends a SMS message via external service """
    message_confirmation = None

    if not current_app.bandwidth_api_endpoint:
        raise ConfigurationError("Bandwidth API endpoint not configured")
    elif not current_app.bandwidth_user_id:
        raise ConfigurationError("Bandwidth user ID not configured")
    elif not current_app.bandwidth_app_id:
        raise ConfigurationError("Bandwidth app ID not configured")

    bw_user_id = current_app.bandwidth_user_id
    api_url = f'{current_app.bandwidth_api_endpoint}/users/{current_app.bandwidth_user_id}/messages'
    payload = {
        'to':to_phone,
        'from':from_phone,
        'text': message_body,
        'applicationId':current_app.bandwidth_app_id,
        'tag':'test'
    }
    json_payload = json.dumps(payload)
    rheaders = _create_headers()

    response = requests.post(url = api_url, data=json_payload, headers=rheaders)
    if response.status_code >= 500:
        current_app.logger.error(f'BW Failed with {response.status_code} Error: \n{response.content}')
        raise ServiceProviderError('Remote BW service is currently unavailable. Please contact support')

    response_data = response.json()
    if response.status_code == 202:
        message_confirmation = {
            'from_phone': response_data['from'],
            'to_phone': response_data['to'][0],
            'network_time': response_data['time'],
            'direction': response_data['direction'],
            'segment_count': response_data['segmentCount'],
            'body_text': response_data['text'],
            'message_media': [],
            'provider_message_id': response_data['id'],
            'provider_name': 'bw'
        }

    else:
        raise ServiceProviderError(f'Bandwidth service provider eror returned code: {response.status_code}')
        #raise ServiceProviderError(response_data['errors'][0]['message'])

    return message_confirmation


def download_mms_media(media_uri):
    """ Fetches MMS media file """
    media_uri = None
    # if ',' in media_uri:
    #     media_uri = media_uri.split(',')[-1].strip('}')
    if ',' in media_uri:
        media_parts = media_uri.split(',')
        for media_part_item in media_parts:
            if '.xml' not in media_part_item and '.smil' not in media_part_item:
                media_uri = media_part_item.strip('}')
                break
    
    mms_media_id = media_uri.split('/')[-3]
    mms_seq = media_uri.split('/')[-2]
    mms_file_name = media_uri.split('/')[-1]
    mms_resource_name = '{}/{}/{}'.format(mms_media_id, mms_seq, mms_file_name)

    if not current_app.bandwidth_api_endpoint:
        raise ConfigurationError("Bandwidth API endpoint not configured")
    elif not current_app.bandwidth_user_id:
        raise ConfigurationError("Bandwidth user ID not configured")
    elif not current_app.bandwidth_app_id:
        raise ConfigurationError("Bandwidth app ID not configured")

    bw_user_id = current_app.bandwidth_user_id
    media_api_endpoint = f'{current_app.bandwidth_api_endpoint}/users/{current_app.bandwidth_user_id}/media/{mms_resource_name}'
    rheaders = _create_headers()

    mms_file_path = os.path.join(upload_location, mms_file_name)
    current_app.logger.info(f'JAJ Path is: {mms_file_path}')
    r = requests.get(url = media_api_endpoint, headers=rheaders, stream=True)
    if r.status_code == 200:
        with open(mms_file_path, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

    else: 
        current_app.logger.error(f'JAJ Got bandwidth code: {r.status_code}')
        current_app.logger.error(f'JAJ URL was: {media_api_endpoint}')

    return mms_file_path,  mms_file_name


def _create_headers():
    """ Creates HTTP request headers expected by external service """
    basic_auth_token = _synth_auth_token()
    headers = {
        'Content-Type': 'application/json; charset=utf-8', 
        'Authorization': basic_auth_token
    }

    return headers


def _synth_auth_token():
    """ Prepares Auth Token per external service's spec """
    if not current_app.bandwidth_api_token:
        raise ConfigurationError("Bandwidth API token not configured")
    elif not current_app.bandwidth_api_secret:
        raise ConfigurationError("Bandwidth API secret not configured")

    basic_auth_token_raw = current_app.bandwidth_api_token+":"+current_app.bandwidth_api_secret
    basic_auth_token_bytes = basic_auth_token_raw.encode("utf-8")
    basic_auth_token_encoded = base64.b64encode(basic_auth_token_bytes).decode('ascii')
    basic_auth_token = f'Basic {basic_auth_token_encoded}'
    return basic_auth_token