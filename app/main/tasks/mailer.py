from flask import Flask, render_template
from flask import current_app as app
from app.main.model.client import Client
from app.main.model.credit_report_account import CreditReportData
from app.main.model.template import TemplateAction, Template
from app.main.model.template import TemplateMedium as MailTransport
from app.main.model.organization import Organization
from app.main.model.debt_payment import DebtPaymentSchedule
from app.main.model.address import Address, AddressType
from datetime import datetime


class TemplateMailManager(object):
    BASE_MAILER_TMPL_PATH = "mailer"
    _tmpl = None 
    _client = None
    _account_manager = None
    _debt = None
    _payment_schedule = None
    _appointment = None
    _is_via_fax = False
    _org = None

    def __init__(self, template):
        self._tmpl = template

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client):
        self._client = client

    @property
    def account_manager(self):
        return self._account_manager

    @account_manager.setter
    def account_manager(self, am):
        self._account_manager = am

    @property
    def debt(self):
        return self._debt

    @debt.setter
    def debt(self, debt):
        self._debt = debt

    @property
    def payment(self):
        return self._payment_schedule

    @payment.setter
    def payment(self, pymt):
        self._payment_schedule = pymt

    @property
    def appointment(self):
        return self._appointment

    @appointment.setter
    def appointment(self, appt):
        self._appointment = appt

    @property
    def action(self):
        return self._template.action 

    @property
    def org(self):
        return self._org

    @org.setter
    def org(self, org):
        self._org = org


    def _to_dict(self):
        result = {}
        if self.client:
            result['client'] = self.client
        if self.account_manager:
            result['account_manager'] = self.account_manager
        if self.debt:
            result['debt'] = self.debt
        if self.payment:
            result['payment'] = self.payment
        if self.appointment:
            result['appointment'] = self.appointment
        if self.org:
            result['org'] = self.org

        result['date_now'] = datetime.now().strftime("%m/%d/%Y")
        result['is_via_fax'] = self._is_via_fax

        return result

    def send(self):
        app.logger.info('executing Mail Manager send')

        # check the mail transport 
        transport = self._tmpl.medium
        ## fax
        if transport == MailTransport.FAX.name:
            # debt collector
            if not self.debt.debt_collector:
                raise ValueError("Debt Collector not present for the debt")

            self.client = self.debt.credit_report_account.client

            if self.debt.debt_collector.fax:
                self._is_via_fax = True

            dest = self.client.email
            params = self._to_dict()
            template_file_path = "{}/{}".format(self.BASE_MAILER_TMPL_PATH, self._tmpl.fname)
            html = render_template(template_file_path, **params)

            ## test send mail
            test_send_email(dest, self._tmpl.subject, html)

        elif transport == MailTransport.EMAIL.name or transport == MailTransport.EMAIL_SMS.name:
            # check client is set or not
            if not self.client:
                raise ValueError("Client is not set for the mail manager")
            dest = self.client.email

            params = self._to_dict()
            template_file_path = "{}/{}".format(self.BASE_MAILER_TMPL_PATH, self._tmpl.fname) 
            html = render_template(template_file_path, **params)        
        
            # print(html)

            ## test send mail
            test_send_email(dest, self._tmpl.subject, html)


# PAYMENT_REMINDER
def send_payment_reminder(client_id, payment_schedule_id):
    """
    Send Payment Reminder notification email to client
    : param int client_id: Client Identifier (required)
    : param int payment_schedule_id: Upcoming payment schedule id
    """
    kwargs = {'client_id': client_id, 'payment_schedule_id': payment_schedule_id}
    send_template(TemplateAction.PAYMENT_REMINDER.name, 
                  **kwargs) 

# SPANISH_GENERAL_CALL
def send_spanish_general_call(client_id):
    """
    Send after a phone appointment complete
    : param int client_id: Client Identifier (required)
    """ 
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.SPANISH_GENERAL_CALL.name,
                  **kwargs)

# CANCELLATION_REQUEST
def send_cancellation_request(client_id):
    """
    Send when client status changes to request cancellation
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.CANCELLATION_REQUEST.name,
                  **kwargs)

# NSF_DRAFT_ISSUE
def send_nsf_draft_issue(client_id):
    """
    Send when EPPS eft fails
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.NSF_DRAFT_ISSUE.name,
                  **kwargs)

# HOUR1_APPOINTMENT_REMINDER
def send_hour1_appointment_reminder(client_id, appt_id):
    """
    Send 1 hour appointment reminder to client
    : param int client_id: Client Identifier (required)
    : param int appt_id: Appointment identifier (required)
    """
    kwargs = { 'client_id': client_id, 'appointment_id': appt_id }
    send_template(TemplateAction.HOUR1_APPOINTMENT_REMINDER.name,
                  **kwargs)

# CHANGE_PAYMENT_DATE
def send_change_payment_date(client_id, pymt_id, appt_id):
    """
    Send change payment date notice to client
    : param int client_id: Client Identifier (required)
    : param int pymt_id: Payment Identifier (required)
    : param int appt_id: Appointment identifier (required)
    """
    kwargs = { 'client_id': client_id, 'payment_id': pymt_id, 'appointment_id': appt_id }
    send_template(TemplateAction.CHANGE_PAYMENT_DATE.name,
                  **kwargs)

# DAY1_APPOINTMENT_REMINDER
def send_hour1_appointment_reminder(client_id, appt_id):
    """
    Send 1 day appointment reminder to client
    : param int client_id: Client Identifier (required)
    : param int appt_id: Appointment identifier (required)
    """
    kwargs = { 'client_id': client_id, 'appointment_id': appt_id }
    send_template(TemplateAction.DAY1_APPOINTMENT_REMINDER.name,
                  **kwargs)

# GENERAL_CALL_EDMS
def send_general_call_edms(client_id):
    """
    Send call ack notice
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.GENERAL_CALL_EDMS.name,
                  **kwargs)

# NOIR_SENT_ACK
def send_noir_sent_ack(client_id, debt_id):
    """
    Send noir sent acknowledge
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.NOIR_SENT_ACK.name,
                  **kwargs)

# DAY15_CALL_ACK
def send_call_summary(client_id):
    """
    After 15 day call is marked complete
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.DAY15_CALL_ACK.name,
                  **kwargs)

# SPANISH_INTRO
def send_spanish_intro(client_id):
    """
    Send when 15 day call is marked as "Complete" in the clients CS Schedule
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.SPANISH_INTRO.name,
                  **kwargs)

# NOIR_NOTICE
# FAX
def send_noir_notice(client_id, debt_id):
    """
    Send noir notice to debt collector
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.NOIR_NOTICE.name,
                  **kwargs)

# NON_RESPONSE_NOTICE
# FAX
def send_non_response_notice(client_id, debt_id):
    """
    Send non response notice to debt collector
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.NON_RESPONSE_NOTICE.name,
                  **kwargs)

def send_noir_fdcpa_notice(client_id, debt_id):
    """
    Send fdcpa notice to debt collector
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.NOIR_FDCPA_NOTICE.name,
                  **kwargs)

def send_intro_call(client_id):
    """
    Send account manager contact information
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.INTRO_CALL.name,
                  **kwargs)

# NO_CONTACT_CANCELLATION
def send_no_contact_cancel_notice(client_id):
    """
    Send no contact cancel notification
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.NO_CONTACT_CANCELLATION.name,
                  **kwargs)
    
def send_refund_notice(client_id):
    """
    Send refund processed notice
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.REFUND_ACK.name,
                  **kwargs)

def send_blank_template(client_id):
    """
    Send refund processed notice
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.BLANK_TEMPLATE.name,
                  **kwargs)

# INITIAL_DISPUTE_SENT_ACK
def send_initial_dispute_ack(client_id, debt_id):
    """
    Send initial dispute acknowledgement letter
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.INITIAL_DISPUTE_SENT_ACK.name,
                  **kwargs)
    

# OTHER_DISPUTE_SENT_ACK
def send_other_dispute_ack(client_id, debt_id):
    """
    Send other dispute acknowledgement letter
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.OTHER_DISPUTE_SENT_ACK.name,
                  **kwargs)


# FULLY_DISPUTED_NOTICE
def send_fully_dispute_ack(client_id, debt_id):
    """
    Send fully dispute acknowledgement letter
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.FULLY_DISPUTED_NOTICE.name,
                  **kwargs) 

# NON_RESPONSE_SENT_ACK
def send_non_response_ack(client_id, debt_id):
    """
    Send Non response acknowledgement letter
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.NON_RESPONSE_SENT_ACK.name,
                  **kwargs)

# CLIENT_PORTAL_LOGIN
def send_client_portal_info(client_id):
    """
    Send client portal information
    : param int client_id: Client Identifier (required)
    """
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.CLIENT_PORTAL_LOGIN.name,
                  **kwargs)
 

def send_initial_dispute_mail(client_id, debt_id):
    """
    Send initial dispute mail
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.INITIAL_DISPUTE_MAIL.name,
                  **kwargs)
    

def send_sold_package_mail():
    """
    Send sold package mail
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.SOLD_PACKAGE_MAIL.name,
                  **kwargs)

def send_delete_document_notice():
    pass

def send_add_document_notice():
    pass


def send_template(action, **kwargs):
    """
    Send a message for a given action using the templates.

    :param str action:  template action (required)
    :param dict kwargs
        int client_id: client identifier
        int debt_id: debt identifier 
        int pymnt_schedule_id Payment Schedule identifier
    """
    template = Template.query.filter_by(action=action).first()
    if template is None:
        raise ValueError("Template not found for action {}".format())

    ## template mail manager
    mail_mgr = TemplateMailManager(template) 

    ## client
    if kwargs.get('client_id'):
        client = Client.query.filter_by(id=kwargs.get('client_id')).first()
        if not client:
            raise ValueError("On template send: Client not found {}".format(client_id))

        client_address = Address.query.filter_by(client_id=kwargs.get('client_id'), type=AddressType.CURRENT).first()
        client.address = client_address.address1   
        client.city = client_address.city
        client.state = client_address.state
        client.zip = client_address.zip_code

        # set the client
        mail_mgr.client = client
      
        mail_mgr.account_manager = client.account_manager
        mail_mgr.account_manager.phone = '877-711-3709'
        mail_mgr.account_manager.fax = '877-711-3746'
    
    ## debt
    if kwargs.get('debt_id'):
        debt = CreditReportData.query.filter_by(id=kwargs.get('debt_id')).first()
        if not debt:
            raise ValueError("Debt not found")
        # set the debt
        mail_mgr.debt = debt

    ## payment schedule 
    if kwargs.get('payment_schedule_id'):
        payment_schedule = DebtPaymentSchedule.query.filter_by(id=kwargs.get('payment_schedule_id')).first()
        if not payment_schedule:
            raise ValueError("Payment schedule not found")

        # set the payment 
        mail_mgr.payment = payment_schedule
        # due date
        mail_mgr.payment.due = payment_schedule.due_date.strftime("%m/%d/%Y")
   
    ## appointment
    if kwargs.get('appointment_id'):
        appointment = Appointment.query.filter_by(id=kwargs.get('appointment_id')).first()
        if not appointment:
            raise ValueError("Appointment not found")

        # set the appointment property
        mail_mgr.appointment = appointment
        mail_mgr.appointment.schedule = appointment.scheduled_at.strftime("%m/%d/%Y %H:%M")

    ## Organization
    ## tmp: fetch the first
    org = Organization.query.first()
    mail_mgr.org = org 
    # send the mail
    mail_mgr.send()



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def test_send_email(dest, subject, html):
    msg = MIMEMultipart()
    msg.set_unixfrom('author')
    msg['From'] = 'support@pitzlabs.com'
    msg['To'] = dest
    msg['Subject'] = subject

    # part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    #msg.attach(part1)
    msg.attach(part2)
    
    mailserver = smtplib.SMTP_SSL('smtp.sendgrid.net', '465')
    #mailserver.starttls()
    mailserver.login('apikey', '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')
    mailserver.sendmail('support@pitzlabs.com', dest, msg.as_string())

    mailserver.quit()

