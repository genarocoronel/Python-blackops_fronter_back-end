import datetime
import enum

from app.main.core.rac import RACRoles
from app.main.model.rac import RACRole
from .. import db, flask_bcrypt


class Department(enum.Enum):
    OPENERS = 'openers'
    SALES = 'sales'
    SERVICE = 'service'
    DOCPROC = 'docproc'


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
    department = db.Column(db.String(20), nullable=True)
    personal_phone = db.Column(db.String(25), nullable=False)
    voip_route_number = db.Column(db.String(50), nullable=True)
    pbx_mailbox_id = db.Column(db.String(25), nullable=True, unique=True)
    pbx_caller_id = db.Column(db.String(100), nullable=True, unique=True)
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

    @property
    def is_admin(self):
        admin_roles = RACRoles.ADMIN, RACRoles.SUPER_ADMIN
        if RACRoles.from_str(self.role.name) in admin_roles:
            return True
        return False

    @property
    def is_manager(self):
        manager_roles = RACRoles.DOC_PROCESS_MGR, RACRoles.OPENER_MGR, RACRoles.SALES_MGR, RACRoles.SERVICE_MGR
        if RACRoles.from_str(self.role.name) in manager_roles:
            return True
        return False

    @property
    def is_opener_account(self):
        opener_roles = RACRoles.OPENER_MGR, RACRoles.OPENER_REP
        if RACRoles.from_str(self.role.name) in opener_roles:
            return True
        return False

    @property
    def is_sales_account(self):
        sales_roles = RACRoles.SALES_MGR, RACRoles.SALES_REP
        if RACRoles.from_str(self.role.name) in sales_roles:
            return True
        return False

    @property
    def is_service_account(self):
        service_roles = RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP
        if RACRoles.from_str(self.role.name) in service_roles:
            return True
        return False

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


class UserVoiceCommunication(db.Model):
    __tablename__ = "user_voice_communications"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    voice_communication_id = db.Column(db.Integer, db.ForeignKey('voice_communications.id'), primary_key=True)

    # relationships
    user = db.relationship('User', backref='voice_communication_user_assoc')
    voice_communication = db.relationship('VoiceCommunication', backref='user_voice_communication_assoc')


class UserFaxCommunication(db.Model):
    __tablename__ = "user_fax_communications"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    fax_communication_id = db.Column(db.Integer, db.ForeignKey('fax_communications.id'), primary_key=True)

    # relationships
    user = db.relationship('User', backref='fax_communication_user_assoc')
    fax_communication = db.relationship('FaxCommunication', backref='user_fax_communication_assoc')


class UserCandidateAssignment(db.Model):
    __tablename__ = "user_candidate_assignments"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), primary_key=True, unique=True)

    # relationships
    user = db.relationship('User', backref='candidate_assignment_user_assoc')
    candidate = db.relationship('Candidate', backref='user_candidate_assignment_assoc')


class UserLeadAssignment(db.Model):
    __tablename__ = "user_lead_assignments"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True, unique=True)

    # relationships
    user = db.relationship('User', backref='lead_assignment_user_assoc')
    client = db.relationship('Client', backref='user_lead_assignment_assoc')


class UserClientAssignment(db.Model):
    __tablename__ = "user_client_assignments"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), primary_key=True, unique=True)

    # relationships
    user = db.relationship('User', backref='client_assignment_user_assoc')
    client = db.relationship('Client', backref='user_client_assignment_assoc')
