# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.user_controller import api as user_ns
from .main.controller.auth_controller import api as auth_ns
from .main.controller.appointment_controller import api as appointment_ns
from .main.controller.client_controller import api as client_ns
from .main.controller.lead_controller import api as lead_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='CRM API',
          version='1.0',
          description='a definition of crm web service'
          )

api.add_namespace(user_ns)
api.add_namespace(auth_ns)
api.add_namespace(lead_ns)
api.add_namespace(client_ns)
api.add_namespace(appointment_ns)
