import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


def _convert_bool(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return True if value.lower() in ['true', 'yes'] else False

    return False

# TODO: remove this once we have better handle on configuration in all environments
default_comms_handler_map = {
    "s3-thedeathstarco-jive-recording": {"pbx_system_name": "UNKNOWN", "handler_name": "jive-recording-handler"},
    "ses-thedeathstarco-jive-received": {"pbx_system_name": "UNKNOWN", "handler_name": "jive-email-handler"},
}


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'UtmqEhIIcPuNbXiKLi3Ufk5C6yv8cEiyiiywfsQSdtE=')
    UPLOAD_LOCATION = os.getenv('UPLOAD_LOCATION', f'{basedir}/files')
    PREQUAL_ID_COUNTER_FILE = os.getenv('PREQUAL_ID_COUNTER_LOCATION', f'{basedir}/prequal_id_counter.txt')
    PREQUAL_ID_COUNTER_LOCK_FILE = os.getenv('PREQUAL_ID_COUNTER_LOCATION', f'{basedir}/prequal_id_counter.txt.lock')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    # AWS configuration
    S3_BUCKET_VOICEMAIL = os.environ.get('S3_BUCKET_VOICEMAIL', 'dev-voicemails')
    S3_BUCKET_FAX = os.environ.get('S3_BUCKET_FAX', 'dev-faxes')
    S3_BUCKET_EMAIL = os.environ.get('S3_BUCKET_EMAIL', 'dev-email')
    S3_BUCKET_DOCPROC = os.environ.get('S3_BUCKET_DOCPROC', 'staging-docproc')
    S3_BUCKET_IMPORTS = os.environ.get('S3_BUCKET_IMPORTS', 'staging-candidate-imports')
    JIVE_QUEUE_URL = os.environ.get('JIVE_QUEUE_URL', 'https://sqs.us-west-2.amazonaws.com/450101876349/jive')
    S3_SIGNED_URL_TIMEOUT_SEC = os.environ.get('S3_SIGNED_URL_TIMEOUT_SEC', 3600)
    COMMS_HANDLER_MAP = os.environ.get('COMMS_HANDLER_MAP', default_comms_handler_map)

    SMART_CREDIT_URL = os.environ.get('SMART_CREDIT_URL', 'https://stage-sc.consumerdirect.com')
    SMART_CREDIT_CLIENT_KEY = os.environ.get('SMART_CREDIT_CLIENT_KEY')
    SMART_CREDIT_PUBLISHER_ID = os.environ.get('SMART_CREDIT_PUBLISHER_ID')
    SMART_CREDIT_SPONSOR_CODE = os.environ.get('SMART_CREDIT_SPONSOR_CODE')
    SMART_CREDIT_EMAIL_DOMAIN = os.environ.get('SMART_CREDIT_EMAIL_DOMAIN', 'thedeathstarco.com')

    DATAX_URL = os.environ.get('DATAX_URL', 'https://verihub.com/datax/')
    DATAX_LICENSE_KEY = os.environ.get('DATAX_LICENSE_KEY', '1753b6c00f084840f9dfed9d5735cffc')
    DATAX_PASSWORD = os.environ.get('DATAX_PASSWORD')
    DATAX_CALL_TYPE = os.environ.get('DATAX_CALL_TYPE', 'dkwconsulting-bavnew')

    # Bandwidth API configs
    BANDWIDTH_API_ENDPOINT = os.environ.get('BANDWIDTH_API_ENDPOINT', None)
    BANDWIDTH_APP_ID = os.environ.get('BANDWIDTH_APP_ID', None)
    BANDWIDTH_USER_ID = os.environ.get('BANDWIDTH_USER_ID', None)
    BANDWIDTH_API_TOKEN = os.environ.get('BANDWIDTH_API_TOKEN', None)
    BANDWIDTH_API_SECRET = os.environ.get('BANDWIDTH_API_SECRET', None)

    # JIVE config
    FAX_SENDER = os.environ.get('FAX_SENDER', None)
    FAX_SERVICE_DOMAIN = os.environ.get('FAX_SERVICE_DOMAIN', None)
    FAX_ACCESS_CODE = os.environ.get('FAX_ACCESS_CODE', None)

    # Our own tokens to identify which provider is calling our /sms/register-message webhook API
    # If we change them, we must change the webhook endpoint with corresponding SMS Providers
    REQUIRE_SMS_WEBHOOK_IDS = _convert_bool(os.environ.get('REQUIRE_SMS_WEBHOOK_IDS', True))
    SMS_WEBHOOK_IDENTITIES = os.environ.get('SMS_WEBHOOK_IDENTITIES', None)

    ENABLE_CORS = True
    DEBUG = False
    SMART_CREDIT_HTTP_USER = os.environ.get('SMART_CREDIT_HTTP_USER') or 'documentservicesolutions'
    SMART_CREDIT_HTTP_PASS = os.environ.get('SMART_CREDIT_HTTP_PASS') or 'grapackerown'

    # Docusign server access
    DOCUSIGN_USER_ID = os.getenv('DOCUSIGN_USER_ID', 'b5a198c8-d772-496f-bea2-f814e70f7fbd')
    DOCUSIGN_ACCOUNT_ID = os.getenv('DOCUSIGN_ACCOUNT_ID', '910decab-18f3-4eae-8456-74552da97b03')
    DOCUSIGN_INTEGRATION_KEY = os.getenv('DOCUSIGN_INTEGRATION_KEY', 'a40df05f-4138-42c7-bae0-140a80b73baa')
    DOCUSIGN_RSA_PRIVATE_KEY = os.getenv('DOCUSIGN_RSA_PRIVATE_KEY', 'docsign/rsa_private.key')

    EPPS_USERNAME = os.getenv('EPPS_USERNAME', 'ASOL_API')
    EPPS_PASSWORD = os.getenv('EPPS_PASSWORD', 'b075f05e-79ed-11ea-a215-005056a3526c')

    # Templating module
    TMPL_BASE_DIR = os.getenv('TMPL_DIR', f'{basedir}/templates')
    TMPL_BASE_EMAIL_PATH = os.getenv('TMPL_BASE_EMAIL_PATH', 'mailer')
    TMPL_BASE_SMS_PATH = os.getenv('TMPL_BASE_SMS_PATH', 'sms')
    TMPL_ATTACHMENT_DOC_LOCATION = os.getenv('TMPL_ATTACHMENT_DOC_LOCATION', f'{basedir}/templates/mailer')
    TMPL_DEFAULT_FROM_EMAIL = os.getenv('TMPL_DEFAULT_FROM_EMAIL', 'support@thedeathstarco.com')
    TMPL_DEFAULT_FROM_SMS = os.getenv('TMPL_DEFAULT_FROM_SMS', '')


class DevelopmentConfig(Config):
    DEBUG = True
    postgres_db = os.environ.get('POSTGRES_DB')
    postgres_user = os.environ.get('POSTGRES_USER')
    postgres_password = os.environ.get('POSTGRES_PASSWORD')
    postgres_service = os.environ.get('POSTGRES_SERVICE')
    SQLALCHEMY_DATABASE_URI = f'postgresql://{postgres_user}:{postgres_password}@{postgres_service}/{postgres_db}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENABLE_CORS = True


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'flask_boilerplate_test.db')
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class StagingConfig(Config):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    ENABLE_CORS = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    ENABLE_CORS = True


config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    staging=StagingConfig,
    prod=ProductionConfig
)

key = Config.SECRET_KEY
upload_location = Config.UPLOAD_LOCATION
prequal_id_counter_file = Config.PREQUAL_ID_COUNTER_FILE
prequal_id_counter_lock_file = Config.PREQUAL_ID_COUNTER_LOCK_FILE
