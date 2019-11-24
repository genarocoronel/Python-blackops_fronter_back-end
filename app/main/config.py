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
    SMART_CREDIT_CLIENT_KEY = os.environ.get('SMART_CREDIT_CLIENT_KEY')
    SMART_CREDIT_PUBLISHER_ID = os.environ.get('SMART_CREDIT_PUBLISHER_ID')
    ENABLE_CORS = False
    DEBUG = False
    SMART_CREDIT_HTTP_USER = os.environ.get('SMART_CREDIT_HTTP_USER') or 'documentservicesolutions'
    SMART_CREDIT_HTTP_PASS = os.environ.get('SMART_CREDIT_HTTP_PASS') or 'grapackerown'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'flask_boilerplate_main.db')
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
