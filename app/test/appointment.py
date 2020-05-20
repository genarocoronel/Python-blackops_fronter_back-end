import requests



class AppointmentTest(object):
    _api_service_url = "http://45.76.77.214:5000/api/v1"

    @classmethod
    def new(cls):
        
        params = {
          'scheduled_on':'05/20/2020 11:00',
          'client_id': 'edb67b29-aede-4cac-845f-53b98fbbdbcd',
          'employee_id': 3,
          'note': 'discussion about NOIR notice',
          'summary': 'Client Appointment',
          'loc': '7081002345',
          'reminder_types': 'sms',
        }
        url = "{}/appointments/".format(cls._api_service_url)
    
        resp = requests.post(url, json=params)
        print(resp)
        return resp


    @classmethod
    def update(cls, appt_id, status):
       
        params = {
           'note': 'Client not available',
           'status': status,
        }
        url = "{}/appointments/{}".format(cls._api_service_url, appt_id) 
        
        resp = requests.put(url, json=params)
        return resp

