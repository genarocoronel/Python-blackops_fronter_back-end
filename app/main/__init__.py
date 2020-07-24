import rq
import ast
from cryptography.fernet import Fernet
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from redis import Redis
from werkzeug.contrib.fixers import ProxyFix
from flask_socketio import SocketIO
import logging

from .config import config_by_name

db = SQLAlchemy()
flask_bcrypt = Bcrypt()

# sccket io channel
wscomm = SocketIO()


def create_app(config_name):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(config_by_name[config_name])

    # REQUEST LOGS
    # DEBUG LOGGING 
    if app.config['DEBUG'] is True:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
        
    if app.config['ENABLE_CORS']:
        app.logger.debug('Enabled CORS support')
        CORS(app, resources={r"/*": {"origins": "*"}})

    app.config['ERROR_404_HELP'] = False

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.chnls_key_store = Redis.from_url(app.config['REDIS_URL'], charset="utf-8", decode_responses=True)
    app.queue = rq.Queue('default', connection=app.redis, default_timeout=3600)

    app.cipher = Fernet(app.config['SECRET_KEY'])

    app.s3_bucket_voicemail = app.config['S3_BUCKET_VOICEMAIL']
    app.s3_bucket_fax = app.config['S3_BUCKET_FAX']
    app.s3_bucket_email = app.config['S3_BUCKET_EMAIL']
    app.s3_bucket_docproc = app.config['S3_BUCKET_DOCPROC']
    app.jive_queue_url = app.config['JIVE_QUEUE_URL']
    app.s3_signed_url_timeout_seconds = app.config['S3_SIGNED_URL_TIMEOUT_SEC']

    app.smart_credit_url = app.config['SMART_CREDIT_URL']
    app.smart_credit_client_key = app.config['SMART_CREDIT_CLIENT_KEY']
    app.smart_credit_publisher_id = app.config['SMART_CREDIT_PUBLISHER_ID']
    app.smart_credit_sponsor_code = app.config['SMART_CREDIT_SPONSOR_CODE']
    app.smart_credit_email_domain = app.config['SMART_CREDIT_EMAIL_DOMAIN']
    app.smart_credit_http_user = app.config['SMART_CREDIT_HTTP_USER']
    app.smart_credit_http_pass = app.config['SMART_CREDIT_HTTP_PASS']

    app.datax_url = app.config['DATAX_URL']
    app.datax_call_type = app.config['DATAX_CALL_TYPE']
    app.datax_license_key = app.config['DATAX_LICENSE_KEY']
    app.datax_password = app.config['DATAX_PASSWORD']

    app.bandwidth_api_endpoint = app.config['BANDWIDTH_API_ENDPOINT']
    app.bandwidth_app_id = app.config['BANDWIDTH_APP_ID']
    app.bandwidth_user_id = app.config['BANDWIDTH_USER_ID']
    app.bandwidth_api_token = app.config['BANDWIDTH_API_TOKEN']
    app.bandwidth_api_secret = app.config['BANDWIDTH_API_SECRET']

    app.fax_sender = app.config['FAX_SENDER']
    app.fax_service_domain = app.config['FAX_SERVICE_DOMAIN']
    app.fax_access_code = app.config['FAX_ACCESS_CODE']

    if not app.config['REQUIRE_SMS_WEBHOOK_IDS']:
        app.sms_webhook_identities = None
    else:
        sms_webhook_ids = app.config['SMS_WEBHOOK_IDENTITIES']
        if not sms_webhook_ids or '' == sms_webhook_ids:
            raise Exception('Error gettin SMS_WEBHOOK_IDENTITIES value. We got None.')

        try:
            app.sms_webhook_identities = ast.literal_eval(app.config['SMS_WEBHOOK_IDENTITIES'])
        except Exception as e:
            raise Exception('Error trying to get the SMS webhook identities environment variable.')

    db.init_app(app)
    flask_bcrypt.init_app(app)

    from app.main.channels import ws
    # initialize socketio
    wscomm.init_app(app, 
                    # logger=True, 
                    # engineio_logger=True,
                    message_queue=app.config['REDIS_URL'],
                    path='/channels', 
                    cors_allowed_origins="*",
                    async_mode="gevent")

    return app
