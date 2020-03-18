import datetime

import jwt
from pytz import utc

from app.main.config import key
from app.main.model.rac import RACRole
from app.main.model.blacklist import BlacklistToken
from .. import db, flask_bcrypt


class User(db.Model):
    """ User Model for storing user related details """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    registered_on = db.Column(db.DateTime, nullable=False)

    # relationships
    rac_role_id = db.Column(db.Integer, db.ForeignKey('rac_role.id', name='fk_user_rac_role_id'))
    role = db.relationship(RACRole, uselist=False)

    # fields
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
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

    @property
    def full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __repr__(self):
        return "<User '{}'>".format(self.username)


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
        now = datetime.datetime.utcnow()
        duration = now - self.datetime.utcnow()

        # password reset expires in 24 hours / 1 day
        if self.has_activated or duration.days >= 1:
            return True
        return False


class UserPBXNumber(db.Model):
    __tablename__ = "user_pbx_numbers"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    pbx_number_id = db.Column(db.Integer, db.ForeignKey('pbx_numbers.id'), primary_key=True)

    # relationships
    user = db.relationship('User', backref='pbx_number_user_assoc')
    pbx_number = db.relationship('PBXNumber', backref='user_pbx_number_assoc')
