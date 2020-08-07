from .. import db
from sqlalchemy.orm import backref

class RACResource(db.Model):
    """ Represents a RAC Resource """
    __tablename__ = "rac_resource"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # name of the resource
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))

    
class RACPermission(db.Model):
    __tablename__ = "rac_permission"

    # Relationships
    rac_role_id = db.Column(db.Integer, db.ForeignKey('rac_role.id', name='fk_rac_permission_rac_role_id'), primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('rac_resource.id', name='fk_rac_permission_resource_id'), primary_key=True)

    rac_role =  db.relationship('RACRole', backref=backref('permissions', cascade="all, delete-orphan"))
    resource =  db.relationship('RACResource', backref=backref('permissions', cascade="all, delete-orphan"))

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



