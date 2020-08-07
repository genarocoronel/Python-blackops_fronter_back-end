import requests
from datetime import datetime
import time


class RegressionTest(object):
    _token = None
    _candidate_id = None
    _lead_id = None
    _client_id = None
    _doc_id = None
    _user_id = None
    
    _get_apis = [
        {'api': 'candidates/filter', 'get_candidate_id': True, 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/income-sources', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/monthly-expenses', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/contact_numbers', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/communications', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/credit-report/account/credentials', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/employments', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/addresses', 'roles': ['admin', 'opener']},
        {'api': 'candidates/{{candidate_id}}/doc', 'roles': ['admin', 'opener']},
        {'api': 'candidates/imports', 'roles': ['admin', 'opener']},
        {'api': 'leads/filter', 'get_lead_id': True, 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'leads/{{lead_id}}/income-sources', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/contact_numbers', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/addresses', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/communications', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        # communication id
        {'api': 'leads/{{lead_id}}/monthly-expenses', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/employments', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/credit-report/debts', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        #{'api': 'leads/{{lead_id}}/credit-report/account/pull', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/coclient', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/checklist', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/payment/plan', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        #{'api': 'leads/{{lead_id}}/amendment/plan', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/payment/schedule', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'leads/{{lead_id}}/docs', 'roles': ['admin', 'salesmgr', 'servicemgr', 'docprocmgr']},
        {'api': 'clients', 'get_client_id': True, 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/income-sources', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/monthly-expenses', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/appointments', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/employments', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/contact_numbers', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/addresses', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/communications', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/credit-report/debts', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/service-schedule', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/docs', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/tasks', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'clients/{{client_id}}/teamrequests', 'roles': ['admin', 'servicemgr', 'salesmgr']},
        {'api': 'clients/{{client_id}}/payment/contract', 'roles': ['admin', 'salesmgr', 'servicemgr',]},
        {'api': 'appointments', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'campaigns', 'roles': ['admin', 'openermgr', 'salesmgr', 'servicemgr']},
        {'api': 'campaigns/pin-phone-nums', 'roles': ['admin', 'openermgr', 'salesmgr', 'servicemgr']},
        {'api': 'campaigns/report', 'roles': ['admin', 'openermgr', 'salesmgr', 'servicemgr']},
        {'api': 'collectors', 'roles': ['admin', 'docprocmgr']},
        {'api': 'creditors', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'debtpayment/eft-fee', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'creditors', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'docproc', 'get_doc_id': True, 'roles': ['admin',  'docprocmgr']},
        {'api': 'docproc/{{doc_id}}/file',  'roles': ['admin', 'docprocmgr']},
        {'api': 'lead-distro/agents', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'tasks', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'teams', 'roles': ['admin',  'servicemgr']},
        {'api': 'teams/service/requests', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'tickets', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'users', 'get_user_id': True, 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'users/{{user_id}}/numbers', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'users/{{user_id}}/tasks', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/clients_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/sales_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/ach_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/future_draft_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/debt_collector_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/creditor_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/task_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/days_delinquent_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/eft_return_fee_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/post_mail_print_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/team_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/staff_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/debt_mgmt_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/notification_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
        {'api': 'reports/status_report/view', 'roles': ['admin', 'salesmgr', 'servicemgr']},
    ]

    def __init__(self, server):
        self._main_url = "http://{}/api/v1/".format(server)

    def _login(self):
        print("Testing => login")
        path = 'auth/login'
        params = {
            'username': self._username,
            'password': self._password,
        }
        response = self._post(path, params)
        #print(response.content['token'])
        assert response.status_code == 200
        data = response.json()
        self._token = data['user']['token']
        print('success')

    def _post(self, path, params):
        url = "{}{}".format(self._main_url, path)
        headers = {}
        if self._token:
            headers = {'Authorization': '{}'.format(self._token)}
        resp = requests.post(url, json=params, headers=headers)
        return resp

    def _get(self, path, params={}):
        url = "{}{}".format(self._main_url, path)
        headers = {}
        if self._token:
            headers = {'Authorization': '{}'.format(self._token)}
        resp = requests.get(url, headers=headers)
        return resp

    def _test_get_apis(self):
        for api_data in self._get_apis:
            path = api_data['api']
            if '{{lead_id}}' in path:
                if not self._lead_id:
                    continue
                path = path.replace('{{lead_id}}', self._lead_id) 
            elif '{{candidate_id}}' in path:
                if not self._candidate_id:
                    continue 
                path = path.replace('{{candidate_id}}', self._candidate_id) 
            elif '{{client_id}}' in path:
                if not self._client_id:
                    continue 
                path = path.replace('{{client_id}}', self._client_id) 
            elif '{{doc_id}}' in path:
                if not self._doc_id:
                    continue 
                path = path.replace('{{doc_id}}', self._doc_id) 
            elif '{{user_id}}' in path:
                if not self._user_id:
                    continue 
                path = path.replace('{{user_id}}', self._user_id) 

            print("Testing ==> {}".format(path))
            response = self._get(path)
            expected_code = 200
            if self._role not in api_data['roles']:
                expected_code = 403

            try:
                assert response.status_code == expected_code, 'Test case failed'
                if expected_code == 200:
                    if 'get_lead_id' in api_data:
                        result = response.json()
                        leads = result['data']
                        if len(leads) > 0:
                            self._lead_id = leads[0]['public_id']
                    elif 'get_candidate_id' in api_data:
                        result = response.json()
                        candidates = result['candidates']
                        if len(candidates) > 0:
                            self._candidate_id = candidates[0]['public_id']
                    elif 'get_client_id' in api_data:
                        result = response.json()
                        clients = result['data']
                        if len(clients) > 0:
                            self._client_id = clients[0]['public_id']
                    elif 'get_doc_id' in api_data:
                        result = response.json()
                        docs = result['data']
                        if len(docs) > 0:
                            self._doc_id = docs[0]['public_id']
                    elif 'get_user_id' in api_data:
                        result = response.json()
                        users = result['data']
                        if len(users) > 0:
                            self._user_id = users[0]['public_id']

                print('test successful')
            except AssertionError:
                print('###############  WARNING :: Test case failed  #################')
                continue

            time.sleep(1)

    def run(self, role='admin', uname=None, pswd=None):
        self._role = role
        self._username = uname
        self._password = pswd

        # login
        self._login()
        time.sleep(1)
        self._test_get_apis()
