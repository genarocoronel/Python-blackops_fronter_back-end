import requests
import unittest


class TestFilters(unittest.TestCase):
   def __init__(self, host):
       self._host = host

   def _case1(self):
       print("Testing Case 1")
       # _state==ca && disposition == contact  || first_name == sven 
       response = requests.get("http://{}/api/v1/candidates/filter?_limit=25&_order=desc&_sort=estimated_debt&_q=state:ca,disposition:contact,first_name&_search=sven&_page_number=1&_dt=inserted_on&_from=01/01/2020".format(self._host))
       result = response.json()
       self.assertIn('page_number', result)

   # multiple fields with common search value
   def _case2(self):
       print("Testing Case 2")
       response = requests.get("http://{}/api/v1/candidates/filter?_limit=25&_order=desc&_sort=estimated_debt&_q=state,first_name&_search=ca&_page_number=1".format(self._host))
       result = response.json()
       self.assertIn('page_number', result)
   # status enum string 
   def _case3(self):
       print("Testing Case 3")
       response = requests.get("http://{}/api/v1/candidates/filter?_limit=25&_order=desc&_sort=estimated_debt&_q=status&_search=working&_page_number=1".format(self._host))
       result = response.json()
       self.assertIn('page_number', result)
   # server error
   # wrong field
   def _case4(self):
       print("Testing Case 4")
       response = requests.get("http://{}/api/v1/candidates/filter?_limit=25&_order=desc&_sort=estimated_debt&_q=status,zipcode&_search=working&_page_number=1".format(self._host))
       result = response.json()
       self.assertIn('Error', result['message'])

   def run(self):
       # run cases
       self._case1()
       self._case2()
       self._case3()
       self._case4()
