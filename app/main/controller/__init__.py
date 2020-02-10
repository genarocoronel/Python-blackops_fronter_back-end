import datetime

from app.main.model.client import ClientType
from app.main.service.client_service import get_client


def _convert_payload_datetime_values(payload, *keys):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    if isinstance(payload, list):
        for item in payload:
            for key in keys:
                if key in item.keys():
                    try:
                        item[key] = datetime.datetime.strptime(item.get(key), datetime_format)
                    except ValueError:
                        item[key] = None
    elif isinstance(payload, dict):
        for key in keys:
            if key in payload.keys():
                try:
                    payload[key] = datetime.datetime.strptime(payload.get(key), datetime_format)
                except TypeError:
                    payload[key] = None


def _handle_get_client(public_id, client_type=ClientType.client):
    client = get_client(public_id, client_type=client_type)
    if not client:
        response_object = {
            'success': False,
            'message': f'{client_type.value.capitalize()} does not exist'
        }
        return None, response_object
    else:
        return client, None


def _handle_get_credit_report(client):
    account = client.credit_report_account
    if not account:
        response_object = {
            'success': False,
            'message': 'Credit Report Account does not exist'
        }
        return None, response_object
    else:
        return account, None