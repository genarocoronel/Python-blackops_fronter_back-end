import requests
from flask import current_app

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/vnd.cd.signup-api.v1.1+json'
}


class LockedException(Exception):
    pass


def _handle_errors(response):
    json_response = response.json()

    if response.ok:
        return json_response, None
    else:
        message = json_response['errors'][0]['message']

        if response.status_code == 422:
            return json_response, message

        if response.status_code == 423:
            raise LockedException(message)

        raise Exception(message)


def start_signup(data):
    response = requests.get('https://stage-sc.consumerdirect.com/api/signup/start',
                            headers=headers,
                            params={
                                'clientKey': current_app.smart_credit_client_key,
                                'ADID': data.get('ad_id'),
                                'AID': data.get('affiliate_id'),
                                'CID': data.get('campaign_id'),
                                'PID': current_app.smart_credit_publisher_id,
                                'channel': data.get('channel')
                            })
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def does_email_exist(email, tracking_token):
    response = requests.get('https://stage-sc.consumerdirect.com/api/signup/validate/email',
                            headers=headers,
                            params={
                                'clientKey': current_app.smart_credit_client_key,
                                'email': email,
                                'trackingToken': tracking_token
                            })
    _, error = _handle_errors(response)
    if error:
        return True, error
    else:
        return False, None


def does_ssn_exist(customer_token, ssn, tracking_token):
    response = requests.get('https://stage-sc.consumerdirect.com/api/signup/validate/ssn',
                            headers=headers,
                            params={
                                'clientKey': current_app.smart_credit_client_key,
                                'ssn': ssn,
                                'customerToken': customer_token,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        return True, error
    else:
        return False, None


def create_customer(data, tracking_token, sponsor_code=None, plan_type=None):
    data = {
        'clientKey': current_app.smart_credit_client_key,
        'email': data.get('email'),
        'firstName': data.get('first_name'),
        'lastName': data.get('last_name'),
        'homeAddress.zip': data.get('zip'),
        'homePhone': data.get('phone'),
        'password': data.get('password'),
        'trackingToken': tracking_token
    }
    if sponsor_code:
        data.update({'sponsorCodeString': sponsor_code})

    if plan_type:
        data.update({'planType': plan_type or 'SPONSORED'})

    response = requests.post('https://stage-sc.consumerdirect.com/api/signup/customer/create',
                             headers=headers,
                             data=data)

    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def get_customer_security_questions(tracking_token):
    response = requests.get('https://stage-sc.consumerdirect.com/api/signup/security-questions',
                            headers=headers,
                            params={
                                'clientKey': current_app.smart_credit_client_key,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result['securityQuestions']


def update_customer(customer_token, data, tracking_token):
    optional_fields = {'confirmTermsBrowserIpAddress': 'ip_address', 'homeAddress.city': 'city',
                       'homeAddress.state': 'state', 'homeAddress.street2': 'street2',
                       'identity.ssn': 'ssn', 'identity.ssnPartial': 'ssn4', 'isConfirmedTerms': 'terms_confirmed',
                       'securityQuestionAnswer.answer': 'security_question_answer',
                       'securityQuestionAnswer.securityQuestionId': 'security_question_id'}
    payload = {
        'clientKey': current_app.smart_credit_client_key,
        'customerToken': customer_token,
        'firstName': data.get('first_name'),
        'lastName': data.get('last_name'),
        'homeAddress.street': data.get('street'),
        'homeAddress.zip': data.get('zip'),
        'homePhone': data.get('phone'),
        'identity.birthDate': data.get('dob'),  # Customer's birth date in the format of MM/dd/yyyy
        'isBrowserConnection': False,
        'trackingToken': tracking_token
    }
    optionally_add_to_payload(optional_fields, payload=payload, data=data)
    response = requests.post('https://stage-sc.consumerdirect.com/api/signup/customer/update/identity',
                             headers=headers.update({'Content-Type': 'application/x-www-form-urlencoded'}),
                             data=payload)
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def get_id_verification_question(customer_token, tracking_token):
    response = requests.get('https://stage-sc.consumerdirect.com/api/signup/id-verification',
                            headers=headers,
                            params={
                                'clientKey': current_app.smart_credit_client_key,
                                'customerToken': customer_token,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def answer_id_verification_questions(customer_token, data, tracking_token):
    payload = {
        'clientKey': current_app.smart_credit_client_key,
        'customerToken': customer_token,
        'trackingToken': tracking_token,
        'idVerificationCriteria.referenceNumber': data.get('reference_number')
    }
    for answer_key, answer_value in data.get('answers').items():
        payload[f'idVerificationCriteria.{answer_key}'] = answer_value

    response = requests.post('https://stage-sc.consumerdirect.com/api/signup/id-verification',
                             headers=headers,
                             data=payload)
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def complete_credit_account_signup(customer_token, tracking_token):
    payload = {
        'clientKey': current_app.smart_credit_client_key,
        'customerToken': customer_token,
        'trackingToken': tracking_token,
    }
    response = requests.post('https://stage-sc.consumerdirect.com/api/signup/complete',
                             headers=headers,
                             data=payload)
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def optionally_add_to_payload(optional_keys, payload, data):
    for value, key in optional_keys.items():
        if key in data:
            payload.update({value: data[key]})


if __name__ == '__main__':
    signup_data = {'adid': 1000, 'aid': 1662780, 'cid': 'ABR:DBL_OD_WOULDYOULIKETOADD_041615', 'pid': '12345',
                   'channel': 'paid'}
    start_signup(signup_data)
