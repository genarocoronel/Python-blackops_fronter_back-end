import requests
from lxml import html

from app.main.core.errors import ServiceProviderError, ServiceProviderLockedError
from flask import current_app as app

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/vnd.cd.signup-api.v1.1+json'
}


def start_signup_session():
    """ Starts a Smart Credit signup session for a new customer """
    app.logger.info("Creating a Credit Report signup session.")
    response = requests.get(f'{app.smart_credit_url}/api/signup/start',
                            headers=headers,
                            params={
                                'clientKey': app.smart_credit_client_key,
                                'PID': app.smart_credit_publisher_id
                            })
    result, error = _handle_errors(response)

    if error:
        app.logger.error(f'Smart Credit service error while staring a signup session, {str(error)}')
        raise Exception(str(error))
    
    signup_session = {
        'customer_token': result.get('customerToken'),
        'provider': result.get('provider'),
        'tracking_token': result.get('trackingToken'),
        'plan_type': result.get('planType'),
        'financial_obligation_met': result.get('financialObligationMet')
    }

    return signup_session


def does_email_exist(email, tracking_token):
    app.logger.info("Checking Smart Credit to see if email exists.")
    response = requests.get(f'{app.smart_credit_url}/api/signup/validate/email',
                            headers=headers,
                            params={
                                'clientKey': app.smart_credit_client_key,
                                'email': email,
                                'trackingToken': tracking_token
                            })
    _, error = _handle_errors(response)
    if error:
        app.logger.error(f'Smart Credit service error while checking if email exists, {str(error)}')
        return True, error
    
    return False, None


def does_ssn_exist(customer_token, ssn, tracking_token):
    app.logger.info("Checking Smart Credit to see if SSN exists.")
    response = requests.get(f'{app.smart_credit_url}/api/signup/validate/ssn',
                            headers=headers,
                            params={
                                'clientKey': app.smart_credit_client_key,
                                'ssn': ssn,
                                'customerToken': customer_token,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        app.logger.error(f'Smart Credit service error while checking if SSN exists, {str(error)}')
        return True, error
    
    return False, None


def create_customer(data, tracking_token, sponsor_code=None, plan_type=None):
    app.logger.info("Creating a Smart Credit customer.")
    data = {
        'clientKey': app.smart_credit_client_key,
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

    response = requests.post(f'{app.smart_credit_url}/api/signup/customer/create',
                             headers=headers,
                             data=data)

    result, error = _handle_errors(response)
    if error:
        app.logger.error(f'Smart Credit service error while creating external customer, {str(error)}')
        raise ServiceProviderError(str(error))
    
    new_customer_result = {
        'customer_token': result.get('customerToken'),
        'is_financial_obligation_met': result.get('isFinancialObligationMet'),
        'plan_type': result.get('planType')
    }
    return new_customer_result


def get_customer_security_questions(tracking_token):
    app.logger.info("Getting Security Questions from Smart Credit.")
    response = requests.get(f'{app.smart_credit_url}/api/signup/security-questions',
                            headers=headers,
                            params={
                                'clientKey': app.smart_credit_client_key,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        app.logger.error(f'Smart Credit service error while getting security questions, {str(error)}')
        raise ServiceProviderError(str(error))
    
    return result['securityQuestions']


def update_customer(customer_token, data, tracking_token):
    app.logger.info("Updating Smart Credit customer info.")
    optional_fields = {'confirmTermsBrowserIpAddress': 'ip_address', 'homeAddress.city': 'city',
                       'homeAddress.state': 'state', 'homeAddress.street2': 'street2',
                       'identity.ssn': 'ssn', 'identity.ssnPartial': 'ssn4', 'isConfirmedTerms': 'terms_confirmed',
                       'securityQuestionAnswer.answer': 'security_question_answer',
                       'securityQuestionAnswer.securityQuestionId': 'security_question_id'}
    payload = {
        'clientKey': app.smart_credit_client_key,
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
    response = requests.post(f'{app.smart_credit_url}/api/signup/customer/update/identity',
                             headers=headers.update({'Content-Type': 'application/x-www-form-urlencoded'}),
                             data=payload)
    result, error = _handle_errors(response)

    if error:
        app.logger.error(f'Smart Credit service error while updating a Customer, {str(error)}')
        raise ServiceProviderError(str(error))
    
    return result


def get_id_verification_question(customer_token, tracking_token):
    app.logger.info("Getting Identity Verification Questions from Smart Credit.")
    app.logger.debug(
        f'get_id_verification_question {app.smart_credit_url}/api/signup/id-verification, {app.smart_credit_client_key}, {customer_token}, {tracking_token}')
    response = requests.get(f'{app.smart_credit_url}/api/signup/id-verification',
                            headers=headers,
                            params={
                                'clientKey': app.smart_credit_client_key,
                                'customerToken': customer_token,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        app.logger.error(f'Smart Credit service error while getting verification questions, {str(error)}')
        raise ServiceProviderError(str(error))
    
    return result


def answer_id_verification_questions(data, customer_token, tracking_token):
    app.logger.info("Answering Verification Questions with Smart Credit.")
    payload = {
        'clientKey': app.smart_credit_client_key,
        'customerToken': customer_token,
        'trackingToken': tracking_token,
        'idVerificationCriteria.referenceNumber': data.get('reference_number')
    }
    
    for answer_key, answer_value in data.get('answers').items():
        payload[f'idVerificationCriteria.{answer_key}'] = answer_value

    response = requests.post(f'{app.smart_credit_url}/api/signup/id-verification',
                             headers=headers,
                             data=payload)
    result, error = _handle_errors(response)
    if error:
        app.logger.error(f'Smart Credit service error while answering verification questions, {str(error)}')
        raise ServiceProviderError(str(error))
    
    return result


def complete_credit_account_signup(customer_token, tracking_token):
    app.logger.info("Completing Smart Credit account signup.")
    payload = {
        'clientKey': app.smart_credit_client_key,
        'customerToken': customer_token,
        'trackingToken': tracking_token,
    }
    response = requests.post(f'{app.smart_credit_url}/api/signup/complete',
                             headers=headers,
                             data=payload)
    result, error = _handle_errors(response)
    if error:
        app.logger.error(f'Smart Credit service error while completing account signup, {str(error)}')
        raise ServiceProviderError(str(error))
    
    return result


def fetch_security_questions(tracking_token):
    app.logger.info("Fetching Security Questions from Smart Credit.")
    response = requests.get(f'{app.smart_credit_url}/api/signup/security-questions',
                            headers=headers,
                            params={
                                'clientKey': app.smart_credit_client_key,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)

    if error:
        app.logger.error(f'Smart Credit service error while fetching security questions, {str(error)}')
        raise ServiceProviderError(str(error))
    
    return result


def answer_security_question(customer_token, tracking_token, data):
    app.logger.info("Answering Security Questions with Smart Credit.")
    try:
        assert data.get('security_question_id'), 'security_question_id is required'
        assert data.get('security_question_answer'), 'security_question_answer is required'
        return update_customer(customer_token=customer_token, data=data, tracking_token=tracking_token)
    except AssertionError as ae:
        app.logger.error(f'Smart Credit service assert error while answering verification questions, {str(ae)}')
        raise ServiceProviderError(f'Malformed payload: {str(ae)}')


def optionally_add_to_payload(optional_keys, payload, data):
    app.logger.info("Adding optional payload to Smart Credit API call data.")
    for value, key in optional_keys.items():
        if key in data:
            payload.update({value: data[key]})


def activate_smart_credit_insurance(username, password):
    app.logger.info("Activating Smart Credit insurance")
    with login_with_session(username, password) as session:
        response = session.post(f'{app.smart_credit_url}/member/id-fraud-insurance/register.htm',
                                auth=(app.smart_credit_http_user, app.smart_credit_http_pass))

        if response.text.find("Insurance Activated") != -1:
            return "Successfully registered id fraud insurance"
        else:
            app.logger.error(f'Could not register for fraud insurance, {response.text}')
            raise ServiceProviderError(f'Could not register for fraud insurance {response.text}')


def login_with_session(username, password):
    app.logger.info("Logging in to Smart Credit with session")
    with requests.Session() as session:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
        }
        session.headers.update(headers)
        response = session.get(f'{app.smart_credit_url}/login/',
                               auth=(app.smart_credit_http_user, app.smart_credit_http_pass))
        tree = html.fromstring(response.text)
        authenticity_token = list(set(tree.xpath("//input[@name='_csrf']/@value")))[0]
        payload = {'_csrf': authenticity_token, 'loginType': 'CUSTOMER',
                   'j_username': username, 'j_password': password}
        session.headers.update({'Referer': f'{app.smart_credit_url}/login/'})
        session.post(f'{app.smart_credit_url}/login', data=payload,
                     auth=(app.smart_credit_http_user, app.smart_credit_http_pass))
        
        return session


def _handle_errors(response):
    if response.status_code >= 500:
        app.logger.error(f'Smart Credit Failed with {response.status_code} Error: \n{response.content}')
        return None, 'Smart Credit is currently unavailable. Please contact support'

    json_response = response.json()
    if response.ok:
        return json_response, None
    else:
        message = json_response['errors'][0]['message']

        if response.status_code == 422:
            return json_response, message

        if response.status_code == 423:
            raise ServiceProviderLockedError(message)

        raise ServiceProviderError(message)


if __name__ == '__main__':    
    start_signup_session()
