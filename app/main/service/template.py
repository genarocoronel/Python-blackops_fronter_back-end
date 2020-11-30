from app.main.model.template import Template
from app.main.model.address import Address, AddressType
from app.main.model.client import Client
from app.main.model.user import User
from app.main.model.organization import Organization
from datetime import datetime
from flask import render_template
from flask import current_app as app


class TemplateView(object):

    def __init__(self, public_id):
        self._tmpl = Template.query.filter_by(public_id=public_id).first()
        self._client = None
        self._account_manager = None
        self._org = None

    @property
    def client(self):
        return self._client

    @property
    def account_manager(self):
        return self._account_manager

    @property
    def org(self):
        return self._org

    @staticmethod
    def list(edit=True):
        templates = Template.query.filter_by(is_editable=edit).all()
        return templates

    def send_mail(self, params):
        client_id = params.get('client_id')
        if client_id is None:
            raise ValueError('Client ID param not found')
         
        client = Client.query.filter_by(public_id=client_id).first() 
        if client is None:
            raise ValueError('Client not found')

        content = params.get('content', '')
        subject = params.get('subject', '')
        
        # send to the task manager
        func = 'send_composed_mail' 
        app.queue.enqueue('app.main.tasks.mailer.{}'.format(func), 
                          client.id, 
                          subject,
                          content,
                          failure_ttl=300)
    
    def render_mail_content(self, params):
        client_id = params.get('client_id')
        if client_id is None:
            raise ValueError('Client ID param not found')
 
        req_user = g.current_user
        user = req_user['user_obj']

        if self._tmpl is None:
            raise ValueError('Mail Template not found')

        # render only editable templates
        if self._tmpl.is_editable is False:
            raise ValueError('Mail Template is not editable')
        
        # get client
        client = Client.query.filter_by(public_id=client_id).first() 
        if client is None:
            raise ValueError('Client not found')

        client_address = Address.query.filter_by(client_id=client.id, type=AddressType.CURRENT).first()
        client.address = client_address.address1
        client.city = client_address.city
        client.state = client_address.state
        client.zip = client_address.zip_code
        self._client = client         

        if client.account_manager:
            self._account_manager = client.account_manager
        else:
            self._account_manager = user
      
        # TODO replace with user pbx profile 
        self._account_manager.phone = '877-711-3709'
        self._account_manager.fax = '877-711-3746'
        
        org = Organization.query.first()
        self._org = org

        content = self._render_template() 
        return {
            'public_id': self._tmpl.public_id,
            'name': self._tmpl.title,
            'content': content,
        }

    def _render_template(self):
        tmpl_base_dir = 'mailer'
        if 'TMPL_BASE_EMAIL_PATH' in app.config:
            tmpl_base_dir = app.config['TMPL_BASE_EMAIL_PATH']

        template_file_path = "{}/{}".format(tmpl_base_dir, self._tmpl.fname)
        params = self._to_dict()
        html = render_template(template_file_path, **params)
        return html

         
    def _to_dict(self):
        result = {}
        if self.client:
            result['client'] = self.client
        if self.account_manager:
            result['account_manager'] = self.account_manager
        if self.org:
            result['org'] = self.org

        result['date_now'] = datetime.utcnow().strftime("%m/%d/%Y")

        return result
