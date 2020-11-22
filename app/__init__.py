# app/__init__.py
import os
from .main.config import _convert_bool

from gevent import monkey
if not _convert_bool(os.environ.get('LOCAL_DEBUG', False)): monkey.patch_all()

#import logging
#logging.basicConfig(level=logging.INFO)

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
from .main.controller.docproc_controller import api as docproc_ns
from .main.controller.collector_controller import api as collector_ns
from .main.controller.creditor_controller import api as creditor_ns
from .main.controller.ticket_controller import api as ticket_ns
from .main.controller.report_controller import api as report_ns
from .main.controller.lead_distro_controller import api as lead_distro_ns
from .main.controller.template_controller import api as template_ns
from .main.portal_api.auth import api as portal_auth_ns
from .main.portal_api.docs import api as portal_doc_ns
from .main.portal_api.budget import api as portal_budget_ns
from .main.portal_api.appointments import api as portal_appointment_ns
from .main.portal_api.messages import api as portal_messages_ns
from .main.portal_api.callsheets import api as portal_callsheet_ns
from .main.portal_api.config import api as portal_config_ns
from .main.portal_api.ticket import api as portal_ticket_ns
from .main.controller.webook_controller import api as webhook_ns
from .main.controller.audit_controller import api as audit_ns


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
api.add_namespace(docproc_ns)
api.add_namespace(collector_ns)
api.add_namespace(creditor_ns)
api.add_namespace(ticket_ns)
api.add_namespace(report_ns)
api.add_namespace(webhook_ns)
api.add_namespace(lead_distro_ns)
api.add_namespace(audit_ns)
api.add_namespace(template_ns)

# Portal API Namespaces
portal_blueprint = Blueprint('portal-api', __name__)
portal_api = Api(portal_blueprint,
        title='Portal API',
        version='1.0',
        description='API for Client Portal resources',
        authorizations=authorizations
        )

portal_api.add_namespace(portal_auth_ns)
portal_api.add_namespace(portal_doc_ns)
portal_api.add_namespace(portal_budget_ns)
portal_api.add_namespace(portal_appointment_ns)
portal_api.add_namespace(portal_messages_ns)
portal_api.add_namespace(portal_callsheet_ns)
portal_api.add_namespace(portal_config_ns)
portal_api.add_namespace(portal_ticket_ns)
