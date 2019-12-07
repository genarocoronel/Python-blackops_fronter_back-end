# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.user_controller import api as user_ns
from .main.controller.auth_controller import api as auth_ns
from .main.controller.appointment_controller import api as appointment_ns
from .main.controller.campaign_controller import api as campaign_ns
from .main.controller.candidate_controller import api as candidate_ns
from .main.controller.client_controller import api as client_ns
from .main.controller.lead_controller import api as lead_ns
from .main.controller.test_controller import api as test_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='CRM API',
          version='1.0',
          description='a definition of crm web service'
          )

api.add_namespace(user_ns)
api.add_namespace(auth_ns)
api.add_namespace(campaign_ns)
api.add_namespace(candidate_ns)
api.add_namespace(lead_ns)
api.add_namespace(client_ns)
api.add_namespace(appointment_ns)
api.add_namespace(test_ns)
