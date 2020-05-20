from flask import Flask, render_template
from flask import current_app as app
from app.main.model.client import Client
from app.main.model.credit_report_account import CreditReportData
from app.main.model.template import TemplateAction, Template, MailBox
from app.main.model.template import TemplateMedium as MailTransport
from app.main.model.organization import Organization
from app.main.model.debt_payment import DebtPaymentSchedule
from app.main.model.address import Address, AddressType
from app.main import db
from datetime import datetime
from app.main.service.email_service import send_mail
from app.main.service.fax_service import send_fax
from app.main.service.sms_service import send_message_to_client
from headless_pdfkit import generate_pdf
from app.main.service.third_party.aws_service import upload_to_docproc


class TemplateMailManager(object):
    FROM_MAILBOX = 'support@thedeathstarco.com'
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
            # fax or post
            if self.debt.debt_collector.fax:
                self._is_via_fax = True

            self.client = self.debt.credit_report_account.client
            tmpl_base_dir = 'mailer'
            if 'TMPL_BASE_EMAIL_PATH' in app.config:
                tmpl_base_dir = app.config['TMPL_BASE_EMAIL_PATH']
            template_file_path = "{}/{}".format(tmpl_base_dir, self._tmpl.fname)
            
            params = self._to_dict()
            html = render_template(template_file_path, **params)
            ts = int(datetime.now().timestamp())            
            doc_name = "{}_{}_{}.pdf".format(self._tmpl.action.lower(), # action
                                             self.client.id, # client id
                                             ts)  # timestamp

            upload_dir_path = app.config['UPLOAD_LOCATION']
            pdfdoc = "{}/{}".format(upload_dir_path, # directory path for the document
                                    doc_name)            

            buff = generate_pdf(html)
            with open(pdfdoc, 'wb') as fd:
                fd.write(buff)

            app.logger.info("Sending fax to client({}) doc({})".format(self.client.id, pdfdoc))
            to_addr = ''
            # send through fax 
            if self._is_via_fax:
                attachments = [pdfdoc, ]
                # to address
                to_addr = self.debt.debt_collector.fax
                send_fax(self.debt.debt_collector.fax,
                         self._tmpl.subject,
                         attachments)             

                # only for testing 
                #send_mail(app.config['TMPL_DEFAULT_FROM_EMAIL'], 
                #          [self.client.email,] , 
                #          self._tmpl.action.lower(), 
                #          html='<html><p>Fax send to debt collector attached.</p></html>', 
                #          attachments=attachments)

            # upload files to S3
            upload_to_docproc(pdfdoc, doc_name) 
            doc_info = [{'name': doc_name, 'path': ''}, ]          
 
            mbox = MailBox(timestamp=datetime.now(),
                           client_id=self.client.id,
                           template_id=self._tmpl.id,
                           to_addr=to_addr,
                           channel=MailTransport.FAX.name,
                           attachments=doc_info) 
            db.session.add(mbox)
            db.session.commit()
                
        elif transport == MailTransport.EMAIL.name or transport == MailTransport.EMAIL_SMS.name:
            # check client is set or not
            if not self.client:
                raise ValueError("Client is not set for the mail manager")

            dest = self.client.email
            attachments = []

            att_dir_path = app.config['TMPL_ATTACHMENT_DOC_LOCATION'] 
            if self._tmpl.attachment:
                att_path = "{}/{}".format(att_dir_path, self._tmpl.attachment)
                attachments = [att_path, ]

            tmpl_base_dir = 'mailer'
            if 'TMPL_BASE_EMAIL_PATH' in app.config:
                tmpl_base_dir = app.config['TMPL_BASE_EMAIL_PATH']
            
            template_file_path = "{}/{}".format(tmpl_base_dir, self._tmpl.fname) 
            params = self._to_dict()
            html = render_template(template_file_path, **params)        
        
            send_mail(app.config['TMPL_DEFAULT_FROM_EMAIL'], 
                      [dest,] , 
                      self._tmpl.subject, 
                      html=html, 
                      attachments=attachments)
            ## test send mail
            #test_send_email(dest, self._tmpl.subject, html)
            mbox = MailBox(timestamp=datetime.now(),
                           client_id=self.client.id,
                           template_id=self._tmpl.id,
                           body=html,
                           to_addr=dest,
                           channel=transport)
            db.session.add(mbox)
            db.session.commit()

        elif transport == MailTransport.SMS.name:
            dest = self.client.email 
            tmpl_base_dir = 'sms'
            if 'TMPL_BASE_SMS_PATH' in app.config:
                tmpl_base_dir = app.config['TMPL_BASE_SMS_PATH']

            template_file_path = "{}/{}".format(tmpl_base_dir, self._tmpl.fname)
            params = self._to_dict()
            msg_body = render_template(template_file_path, **params)
            # send SMS 
            send_message_to_client(client_public_id=self.client.public_id,
                                   from_phone=app.config['TMPL_DEFAULT_FROM_SMS'], # from,
                                   message_body=msg_body,
                                   to_phone=None) 

            mbox = MailBox(timestamp=datetime.now(),
                           client_id=self.client.id,
                           template_id=self._tmpl.id,
                           body=html,
                           to_addr=dest,
                           channel=transport)
            db.session.add(mbox)
            db.session.commit() 


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
def send_day1_appointment_reminder(client_id, appt_id):
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
    

def send_sold_package_mail(client_id, debt_id):
    """
    Send sold package mail
    : param int client_id: Client Identifier (required)
    : param int debt_id: Debt Identifier (required)
    """
    kwargs = { 'client_id': client_id, 'debt_id': debt_id }
    send_template(TemplateAction.SOLD_PACKAGE_MAIL.name,
                  **kwargs)

def send_spanish_welcome_letter(client_id):
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.SPANISH_WELCOME_LETTER.name,
                  **kwargs)

def send_welcome_letter(client_id):
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.WELCOME_LETTER.name,
                  **kwargs)

def send_privacy_policy(client_id):
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.PRIVACY_POLICY.name,
                  **kwargs)

def send_delete_document_notice():
    pass

def send_add_document_notice():
    pass

# SMS 
# text messaging
def send_day3_reminder(client_id):
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.DAY3_REMINDER.name,
                  **kwargs)

def send_day3_spanish_reminder(client_id):
    kwargs = { 'client_id': client_id }
    send_template(TemplateAction.DAY3_REMINDER_SPANISH.name,
                  **kwargs)





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
from email.mime.application import MIMEApplication
import os

def test_send_email(dest, subject, html, attachments=[]):
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

    for f in attachments:
        with open(f, "rb") as fd:
            att_part = MIMEApplication(
                fd.read(),
                Name=os.path.basename(f)
            )
        att_part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
        msg.attach(att_part)
    
    mailserver = smtplib.SMTP_SSL('smtp.sendgrid.net', '465')
    #mailserver.starttls()
    mailserver.login('apikey', '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')
    mailserver.sendmail('support@pitzlabs.com', dest, msg.as_string())

    mailserver.quit()

