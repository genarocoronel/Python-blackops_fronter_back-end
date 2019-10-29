import requests

# client_key = 'f80b0ed5-597c-46a5-9339-d585996b3fe1'
client_key = 'f80b0ed5-597c-46a5-9339-d585996b3fe1'
publisher_id = ''

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
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
    return {
        "trackingToken": "53679db0-093e-11e5-b939-0800200c9a66"
    }
    response = requests.get('https://stage-sc.consumerdirect.com/api/signup/start',
                            headers=headers,
                            params={
                                'clientKey': client_key,
                                'ADID': data.get('ad_id'),
                                'AID': data.get('affiliate_id'),
                                'CID': data.get('campaign_id'),
                                'PID': publisher_id,
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
                                'clientKey': client_key,
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
                                'clientKey': client_key,
                                'ssn': ssn,
                                'customerToken': customer_token,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        return True, error
    else:
        return False, None


def create_customer(data, sponsor_code, tracking_token, plan_type=None):
    return {
        "customerToken": "b3e9f907-8cc8-4e3a-849b-b16c6eb23682",
        "isFinancialObligationMet": False,
        "planType": "SPONSORED",
        "PID": "12345"
    }
    response = requests.post('https://stage-sc.consumerdirect.com/api/signup/customer/create',
                             headers=headers,
                             data={
                                 'clientKey': client_key,
                                 'email': data.get('email'),
                                 'firstName': data.get('first_name'),
                                 'lastName': data.get('last_name'),
                                 'homeAddress.zip': data.get('zip'),
                                 'homePhone': data.get('phone'),
                                 'password': data.get('password'),
                                 'planType': plan_type or 'SPONSORED',
                                 'sponsorCodeString': sponsor_code,
                                 'trackingToken': tracking_token,
                             })
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def get_id_verification_question(customer_token, tracking_token):
    return questions
    response = requests.get('https://stage-sc.consumerdirect.com/api/signup/id-verification',
                            headers=headers,
                            params={
                                'clientKey': client_key,
                                'customerToken': customer_token,
                                'trackingToken': tracking_token
                            })
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def answer_id_verification_questions(customer_token, data, tracking_token):
    response = requests.post('https://stage-sc.consumerdirect.com/api/signup/id-verification',
                             headers=headers,
                             data={
                                 'clientKey': client_key,
                                 'customerToken': customer_token,
                                 'trackingToken': tracking_token,
                                 'idVerificationCriteria.referenceNumber': data.get('reference_number'),
                                 'idVerificationCriteria.answer1': data.get('answer1'),
                                 'idVerificationCriteria.answer2': data.get('answer2'),
                                 'idVerificationCriteria.answer3': data.get('answer3'),
                                 'idVerificationCriteria.answer4': data.get('answer4'),
                                 'idVerificationCriteria.answer5': data.get('answer5')
                             })
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result


def update_customer(customer_token, data, tracking_token):
    response = requests.post('https://stage-sc.consumerdirect.com/api/signup/customer/update/identity',
                             headers=headers,
                             data={
                                 'clientKey': client_key,
                                 'confirmTermsBrowserIpAddress': '',
                                 'customerToken': customer_token,
                                 'firstName': data.get('first_name'),
                                 'lastName': data.get('last_name'),
                                 'homeAddress.city': data.get('city'),
                                 'homeAddress.state': data.get('state'),
                                 'homeAddress.street': data.get('street'),
                                 'homeAddress.street2': data.get('street2'),
                                 'homeAddress.zip': data.get('zip'),
                                 'homePhone': data.get('phone'),
                                 'identity.birthDate': data.get('dob'), # Customer's birth date in the format of MM/dd/yyyy
                                 'identity.ssnPartial': data.get('ssn4'),
                                 'isBrowserConnection': False,
                                 'isConfirmedTerms': data.get('terms_confirmed'),
                                 'securityQuestionAnswer.securityQuestionId': data.get('security_question_id'),
                                 'securityQuestionAnswer.answer': data.get('security_question_answer'),
                                 'trackingToken': tracking_token
                             })
    result, error = _handle_errors(response)
    if error:
        raise Exception(error)
    else:
        return result

questions = {
  "idVerificationCriteria": {
    "referenceNumber": "07271524018421870957",
    "question1": {
      "name": "YEAR_FOUNDED",
      "displayName": "What year was ConsumerDirect (aka PathwayData, aka MyPerfectCredit) founded?",
      "type": "MC",
      "choiceList": {
        "choice": [
          {
            "key": "1980",
            "display": "1980"
          },
          {
            "key": "1969",
            "display": "1969"
          },
          {
            "key": "2012",
            "display": "2012"
          },
          {
            "key": "2003",
            "display": "2003"
          },
          {
            "key": "!(1980^1969^2012^2003)",
            "display": "None of the above"
          }
        ]
      }
    },
    "question2": {
      "name": "NOT_CREDIT_BUREAU",
      "displayName": "Which company is NOT a credit bureau?",
      "type": "MC",
      "choiceList": {
        "choice": [
          {
            "key": "Experian",
            "display": "Experian"
          },
          {
            "key": "ConsumerDirect",
            "display": "ConsumerDirect"
          },
          {
            "key": "Equifax",
            "display": "Equifax"
          },
          {
            "key": "TransUnion",
            "display": "TransUnion"
          },
          {
            "key": "!(Experian^ConsumerDirect^Equifax^TransUnion^)",
            "display": "None of the above"
          }
        ]
      }
    },
    "question3": {
      "name": "INVENTED_INTERNET",
      "displayName": "Who invented the internet?",
      "type": "MC",
      "choiceList": {
        "choice": [
          {
            "key": "J. C. R. Licklider",
            "display": "J. C. R. Licklider"
          },
          {
            "key": "George Clooney",
            "display": "George Clooney"
          },
          {
            "key": "Al Gore",
            "display": "Al Gore"
          },
          {
            "key": "Howard Stark",
            "display": "Howard Stark"
          },
          {
            "key": "!(J. C. R. Licklider^George Clooney^Al Gore^Howard Stark^)",
            "display": "None of the above"
          }
        ]
      }
    }
  }
}

if __name__ == '__main__':
    signup_data = {'adid': 1000, 'aid': 1662780, 'cid': 'ABR:DBL_OD_WOULDYOULIKETOADD_041615', 'pid': '12345',
                   'channel': 'paid'}
    start_signup(signup_data)
