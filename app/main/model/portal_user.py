import datetime

from .. import db, flask_bcrypt

class PortalUser(db.Model):
    """ Represents a Portal User """
    __tablename__ = "portal_users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    registered_on = db.Column(db.DateTime, nullable=False)
    
    email = db.Column(db.String(255), unique=True, nullable=False)
    require_2fa = db.Column(db.Boolean, default=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100))
    challenge_2fa = db.Column(db.String(10))
    invite_token = db.Column(db.String(128))
    is_claimed = db.Column(db.Boolean, default=False)
    is_disabled = db.Column(db.Boolean, default=False)

    # relationships
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', name='fk_portal_user_client_id'), nullable=True)
    client = db.relationship('Client', backref='portal_account', uselist=False,)

    @property
    def password(self):
        raise AttributeError('password: write-only field')

    @password.setter
    def password(self, password):
        """ Sets password """
        self.password_hash = flask_bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return flask_bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<PortalUser '{}'>".format(self.username)

