import rq
from cryptography.fernet import Fernet
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from redis import Redis

from .config import config_by_name

db = SQLAlchemy()
flask_bcrypt = Bcrypt()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('candidate-upload-tasks', connection=app.redis, default_timeout=3600)
    app.cipher = Fernet(app.config['SECRET_KEY'])

    db.init_app(app)
    flask_bcrypt.init_app(app)

    return app