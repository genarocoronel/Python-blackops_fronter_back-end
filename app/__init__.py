# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.user_controller import api as user_ns
from .main.controller.auth_controller import api as auth_ns
from .main.controller.appointment_controller import api as appointment_ns

blueprint = Blueprint('api', __name__)

api = Api(blueprint,
          title='CRM API',
          version='1.0',
          description='a definition of crm web service'
          )

api.add_namespace(user_ns)
api.add_namespace(auth_ns)
api.add_namespace(appointment_ns)
