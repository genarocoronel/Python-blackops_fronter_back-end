import xml.etree.ElementTree as ET

import requests
from flask import current_app


def _build_request(bank_account_number, bank_aba_number, tracking_id, query_type):
    root = ET.Element('DATAXINQUIRY')
    authentication = ET.SubElement(root, 'AUTHENTICATION')
    license_key_node = ET.SubElement(authentication, 'LICENSEKEY')
    license_key_node.text = current_app.datax_license_key
    password_node = ET.SubElement(authentication, 'PASSWORD')
    password_node.text = current_app.datax_password

    query_node = ET.SubElement(root, 'QUERY')

    track_id_node = ET.SubElement(query_node, 'TRACKID')
    track_id_node.text = tracking_id
    query_type_node = ET.SubElement(query_node, 'TYPE')
    query_type_node.text = query_type

    data = ET.SubElement(query_node, 'DATA')
    account_number_node = ET.SubElement(data, 'BANKACCTNUMBER')
    account_number_node.text = bank_account_number
    aba_number_node = ET.SubElement(data, 'BANKABA')
    aba_number_node.text = bank_aba_number

    return root


def validate_bank_account(bank_account_number, bank_aba_number, tracking_id=''):
    request_payload = _build_request(bank_account_number, bank_aba_number, tracking_id, current_app.datax_call_type)

    response = requests.post(current_app.datax_url, data=ET.tostring(request_payload, encoding='utf8', method='xml'),
                             headers={'Content-Type': 'application/xml'})

    if response.ok:
        response_xml = ET.fromstring(response.content)
        response_node = response_xml.find('Response')
        if response_node and (response_node.find('ErrorCode') or response_node.find('ErrorMsg')):
            return None, dict(message=response_node.find('ErrorMsg').text, code=response_node.find('ErrorCode').text)
        else:
            data_node = response_xml.find('BAVSegment')
            routing_number = data_node.find('NewRoutingNumber').text
            bank_name = data_node.find('BankName').text
            aba_number = data_node.find('BankABA').text
            account_number = data_node.find('BankAccount').text
            validation_code = data_node.find('Code').text
            validation_detail = data_node.find('Details').text

            aba_valid = True if data_node.find('Valid').text == 'Y' else False
            acct_valid = True if data_node.find('Pass').text == 'true' else False
            valid = True if aba_valid and acct_valid else False

            return dict(valid=valid, routing_number=routing_number, bank_name=bank_name, aba_number=aba_number,
                        account_number=account_number, validation_code=validation_code,
                        validation_detail=validation_detail), None
    else:
        return None, dict(message='Failed to make call to DataX')
