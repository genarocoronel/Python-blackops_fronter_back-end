from .. import db

class RACPolicy(db.Model):
    __tablename__ = "rac_policy"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)
    is_deny = db.Column(db.Boolean, default=True)

    # Relationships
    rac_role_id = db.Column(db.Integer, db.ForeignKey('rac_role.id', name='fk_rac_policy_rac_role_id'))
    resource_id = db.Column(db.Integer, db.ForeignKey('rac_resource.id', name='fk_rac_policy_resource_id'))
    resource = db.relationship('RACResource', uselist=False)


class RACRole(db.Model):
    """ Represents a RAC Role """
    __tablename__ = "rac_role"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)

    name = db.Column(db.String(30), nullable=False)
    name_friendly = db.Column(db.String(50))
    description = db.Column(db.String(100))

    # Relationships
    policies = db.relationship('RACPolicy', uselist=True, backref='rac_role')


class RACResource(db.Model):
    """ Represents a RAC Resource """
    __tablename__ = "rac_resource"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)
    updated_on = db.Column(db.DateTime)

    resource = db.Column(db.String(30))
    sub_resource = db.Column(db.String(50))
    action = db.Column(db.String(125), nullable=False)
    description = db.Column(db.String(100))
    