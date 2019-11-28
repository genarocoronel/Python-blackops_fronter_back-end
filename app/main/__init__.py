import rq
from cryptography.fernet import Fernet
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from redis import Redis
from werkzeug.contrib.fixers import ProxyFix

from .config import config_by_name

db = SQLAlchemy()
flask_bcrypt = Bcrypt()


def create_app(config_name):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(config_by_name[config_name])

    if app.config['ENABLE_CORS']:
        app.logger.debug('Enabled CORS support')
        CORS(app, resources={r"/*": {"origins": "*"}})

    app.config['ERROR_404_HELP'] = False

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.mailer_file_queue = rq.Queue('mailer-file-tasks', connection=app.redis, default_timeout=3600)
    app.task_queue = rq.Queue('candidate-upload-tasks', connection=app.redis, default_timeout=3600)
    app.spider_queue = rq.Queue('credit-report-spider', connection=app.redis, default_timeout=3600)
    app.cipher = Fernet(app.config['SECRET_KEY'])

    app.smart_credit_url = app.config['SMART_CREDIT_URL']
    app.smart_credit_client_key = app.config['SMART_CREDIT_CLIENT_KEY']
    app.smart_credit_publisher_id = app.config['SMART_CREDIT_PUBLISHER_ID']
    app.smart_credit_sponsor_code = app.config['SMART_CREDIT_SPONSOR_CODE']

    app.datax_url = app.config['DATAX_URL']
    app.datax_call_type = app.config['DATAX_CALL_TYPE']
    app.datax_license_key = app.config['DATAX_LICENSE_KEY']
    app.datax_password = app.config['DATAX_PASSWORD']

    db.init_app(app)
    flask_bcrypt.init_app(app)

    return app