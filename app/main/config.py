import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'UtmqEhIIcPuNbXiKLi3Ufk5C6yv8cEiyiiywfsQSdtE=')
    UPLOAD_LOCATION = os.getenv('UPLOAD_LOCATION', f'{basedir}/files')
    PREQUAL_ID_COUNTER_FILE = os.getenv('PREQUAL_ID_COUNTER_LOCATION', f'{basedir}/prequal_id_counter.txt')
    PREQUAL_ID_COUNTER_LOCK_FILE = os.getenv('PREQUAL_ID_COUNTER_LOCATION', f'{basedir}/prequal_id_counter.txt.lock')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    S3_BUCKET_VOICEMAIL = os.environ.get('S3_BUCKET_VOICEMAIL', 'dev-voicemails')
    S3_BUCKET_FAX = os.environ.get('S3_BUCKET_FAX', 'dev-faxes')
    S3_BUCKET_DOCPROC = os.environ.get('S3_BUCKET_DOCPROC', 'dev-docproc')

    JIVE_QUEUE_URL = os.environ.get('JIVE_QUEUE_URL', 'https://sqs.us-west-2.amazonaws.com/450101876349/jive')

    SMART_CREDIT_URL = os.environ.get('SMART_CREDIT_URL', 'https://stage-sc.consumerdirect.com')
    SMART_CREDIT_CLIENT_KEY = os.environ.get('SMART_CREDIT_CLIENT_KEY')
    SMART_CREDIT_PUBLISHER_ID = os.environ.get('SMART_CREDIT_PUBLISHER_ID')
    SMART_CREDIT_SPONSOR_CODE = os.environ.get('SMART_CREDIT_SPONSOR_CODE')
    SMART_CREDIT_EMAIL_DOMAIN = os.environ.get('SMART_CREDIT_EMAIL_DOMAIN', 'thedeathstarco.com')

    DATAX_URL = os.environ.get('DATAX_URL', 'https://rc.verihub.com/datax/')
    DATAX_LICENSE_KEY = os.environ.get('DATAX_LICENSE_KEY', '1753b6c00f084840f9dfed9d5735cffc')
    DATAX_PASSWORD = os.environ.get('DATAX_PASSWORD')
    DATAX_CALL_TYPE = os.environ.get('DATAX_CALL_TYPE', 'dkwconsulting-bavnew')

    # Bandwidth API configs
    BANDWIDTH_API_ENDPOINT=os.environ.get('BANDWIDTH_API_ENDPOINT', None)
    BANDWIDTH_APP_ID=os.environ.get('BANDWIDTH_APP_ID', None)
    BANDWIDTH_USER_ID=os.environ.get('BANDWIDTH_USER_ID', None)
    BANDWIDTH_API_TOKEN=os.environ.get('BANDWIDTH_API_TOKEN', None)
    BANDWIDTH_API_SECRET=os.environ.get('BANDWIDTH_API_SECRET', None)

    # Our own tokens to identify which provider is calling our /sms/register-message webhook API
    # If we change them, we must change the webhook endpoint with corresponding SMS Providers
    SMS_WEBHOOK_IDENTITIES = os.environ.get('SMS_WEBHOOK_IDENTITIES', None)

    ENABLE_CORS = False
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
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'flask_boilerplate_test.db')
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class StagingConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProductionConfig(Config):
    DEBUG = False
    # uncomment the line below to use postgres
    # SQLALCHEMY_DATABASE_URI = postgres_local_base


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
