# app/__init__.py

from flask_restplus import Api
from flask import Blueprint

from .main.controller.auth_controller import api as auth_ns
from .main.controller.user_controller import api as user_ns
from .main.controller.appointment_controller import api as appointment_ns
from .main.controller.campaign_controller import api as campaign_ns
from .main.controller.candidate_controller import api as candidate_ns
from .main.controller.config_controller import api as config_ns
from .main.controller.client_controller import api as client_ns
from .main.controller.lead_controller import api as lead_ns
from .main.controller.rsign_controller import api as rsign_ns
from .main.controller.debt_payment_controller import api as debtpay_ns
from .main.controller.notes_controller import api as notes_ns
from .main.controller.sms_controller import api as sms_ns
from .main.controller.communication_controller import api as comms_ns
from .main.controller.team_controller import api as team_ns
from .main.controller.task_controller import api as task_ns

blueprint = Blueprint('api', __name__)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(blueprint,
          title='CRM API',
          version='1.0',
          description='a definition of crm web service',
          authorizations=authorizations
          )

api.add_namespace(auth_ns)
api.add_namespace(user_ns)
api.add_namespace(campaign_ns)
api.add_namespace(candidate_ns)
api.add_namespace(config_ns)
api.add_namespace(lead_ns)
api.add_namespace(client_ns)
api.add_namespace(appointment_ns)
api.add_namespace(rsign_ns)
api.add_namespace(debtpay_ns)
api.add_namespace(notes_ns)
api.add_namespace(sms_ns)
api.add_namespace(comms_ns)
api.add_namespace(team_ns)
api.add_namespace(task_ns)
