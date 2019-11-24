import datetime

import jwt
from pytz import utc

from app.main.config import key
from app.main.model.blacklist import BlacklistToken
from .. import db, flask_bcrypt


class User(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)
    require_2fa = db.Column(db.Boolean, default=True)
    title = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(25), nullable=False)
    personal_phone = db.Column(db.String(25), nullable=False)
    voip_route_number = db.Column(db.String(50), nullable=True)
    public_id = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100))

    @property
    def password(self):
        raise AttributeError('password: write-only field')

    @password.setter
    def password(self, password):
        self.password_hash = flask_bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return flask_bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User '{}'>".format(self.username)

    @staticmethod
    def encode_auth_token(user_id):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                key,
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Decodes the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, key)
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'


class UserPasswordReset(db.Model):
    __tablename__ = "password_resets"

    id = db.Column(db.Integer, primary_key=True)
    reset_key = db.Column(db.String(128), unique=True)
    code_hash = db.Column(db.String(100))
    validated = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    datetime = db.Column(db.DateTime(timezone=True), default=datetime.datetime.utcnow())
    user = db.relationship(User, lazy='joined')
    has_activated = db.Column(db.Boolean, default=False)

    @property
    def code(self):
        raise AttributeError('password: write-only field')

    @code.setter
    def code(self, code):
        self.code_hash = flask_bcrypt.generate_password_hash(code).decode('utf-8')

    def check_code(self, code):
        return flask_bcrypt.check_password_hash(self.code_hash, code)

    def is_expired(self):
        now = datetime.datetime.now(tz=utc)
        duration = now - self.datetime

        # password reset expires in 24 hours / 1 day
        if self.has_activated or duration.days >= 1:
            return True
        return False
