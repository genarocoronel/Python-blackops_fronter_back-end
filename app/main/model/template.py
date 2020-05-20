import enum
from app.main import db
from datetime import datetime
from sqlalchemy.orm import backref


class TemplateMode(enum.Enum):
    AUTO = "auto"
    MANUAL = "manual"

class TemplateMedium(enum.Enum):
    FAX = 'fax'    # Priority -- FAX, if not POST
    POST = 'post'  # POST ONLY
    EMAIL_SMS = 'email & sms'  # Email & SMS
    EMAIL = 'email' # EMAIL ONLY
    SMS = 'sms'  # SMS ONLY

class TemplateAction(enum.Enum):
    PAYMENT_REMINDER = "payment_reminder" # pending_payment_notice.html
    SPANISH_GENERAL_CALL = "spanish_general_call"  # spanish_general_call.html
    CANCELLATION_REQUEST = "cancellation_request" # cancellation_request.html, cancellation_request.txt
    NSF_DRAFT_ISSUE = "nsf_draft_issue" # nsf_draft_issue.html , nsf_draft_issue.txt
    HOUR1_APPOINTMENT_REMINDER = "hour1_appointment_reminder" # h1_appointment_reminder.html
    CHANGE_PAYMENT_DATE = "change_payment_date" # change_payment_date.html, change_payment_date.txt
    DAY1_APPOINTMENT_REMINDER = "day1_appointment_reminder" # d1_appointment_reminder.html d1_appointment_reminder.txt
    GENERAL_CALL_EDMS = "general_call_edms" # general_call.html 
    NOIR_SENT_ACK = "noir_sent_ack" # noir_sent_ack.html
    DAY15_CALL_ACK = "day15_call_ack" # d15_call_ack.html 
    SPANISH_INTRO   = "spanish_intro" # spanish_intro.html
    NOIR_NOTICE = "noir_notice"  # noir_common.html
    NON_RESPONSE_NOTICE = "non_response_notice"  # non_response_notice.html
    NOIR_FDCPA_NOTICE = "noir_fdcpa_notice" # fdcpa_insufficient_response.html
    # NOTIFICATION_EPPS_PAYMENT ="Notifiction EPPS Payment"
    INTRO_CALL = "intro_call" # intro_call.html
    NO_CONTACT_CANCELLATION = "no_contact_cancellation" # no_contact_cancel_notice.html
    # REFUND_REQUEST = "refund_request" # refund_request.html
    REFUND_ACK = "refund_ack" # refund_ack.html 
    BLANK_TEMPLATE = "blank_template" # blank_template.html
    INITIAL_DISPUTE_SENT_ACK = "initial_dispute_sent_ack" # initial_dispute_sent_ack.html
    OTHER_DISPUTE_SENT_ACK = "other_dispute_sent_ack" # other_dispute_sent_ack.html 
    FULLY_DISPUTED_NOTICE = "fully_disputed_notice" # fully_disputed_notice.html
    NON_RESPONSE_SENT_ACK = "non_response_sent_ack" # non_response_sent_ack.html
    # SALESPERSON_DECLARATION_EDMS = "Sales Person Declaration EDMS"
    CLIENT_PORTAL_LOGIN = "client_portal_login" # client_portal_login.html
    WELCOME_LETTER = "Welcome Letter"
    SPANISH_WELCOME_LETTER = "Spanish Welcome Letter"
    PRIVACY_POLICY = "Privacy Policy"
    # NSF_DRAFT_ISSUE_SMS = "nsf_draft_issue_sms"  
    INITIAL_DISPUTE_MAIL = "initial_dispute_mail" # initial_dispute_mail.html 
    SOLD_PACKAGE_MAIL = "sold_package_mail" # sold_package_mail.html
    DELETE_DOCMENT_NOTICE = "delete_document_notice" # delete_document_notice.html
    NEW_DOCUMENT_NOTICE = "new_document_notice" # new_document_notice.html
    DAY3_REMINDER = "day3_reminder"  # day3_reminder.txt 
    DAY3_REMINDER_SPANISH = "day3_reminder_spanish" # day3_reminder_spanish.txt

# email, fax or mail templates
class Template(db.Model): 
    """ db model for storing templates used for sending emails/faxes"""
    __tablename__ = "templates"

    # primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)

    # title of the template
    title = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    # path -- file name 
    fname = db.Column(db.String(100), unique=True, nullable=False)
    # atatched document/pdf 
    attachment = db.Column(db.String(100), nullable=True)
    # template action
    action = db.Column(db.String(100), nullable=False)
    # mail subject
    subject = db.Column(db.String(200), nullable=True)
    # trigger mode
    trigger_mode = db.Column(db.String(20), nullable=False, default=TemplateMode.AUTO.name)
    is_uploaded = db.Column(db.Boolean, default=False)
    is_editable = db.Column(db.Boolean, default=False)

    # Notification Medium 
    medium = db.Column(db.String(20), default=TemplateMedium.EMAIL.name)

    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id', name='templates_uploader_id_fkey'))
    uploader = db.relationship('User', backref='uploaded_templates') 

    uploaded_on = db.Column(db.DateTime, nullable=True) 


# mail storage
class MailBox(db.Model):
    """ db model for storing mails send out by the system"""
    __tablename__ = "mailbox"

    # primary key
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)   

    # mail send timestamp
    timestamp = db.Column(db.DateTime, nullable=False)
    
    # client to/for which communication is masde
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='mailbox_client_id_fkey'))
    # template used for creating the message
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id', name='mailbox_template_id_fkey'))

    # relationship
    client = db.relationship('Client', backref='mails')
    template = db.relationship('Template', backref='mails')

    # from address
    from_addr = db.Column(db.String(200), nullable=True)
    # to address
    to_addr = db.Column(db.String(200), nullable=True)
    # mail body 
    body = db.Column(db.Text,  nullable=True)

    # communication channel
    channel = db.Column(db.String(20), default=TemplateMedium.EMAIL.name) 
 
    # attachments - path & name in json format
    # [{'name': 'xyz.doc', 'path': 'https://xyz.com/docs/'}]    
    attachments = db.Column(db.JSON, default={})


