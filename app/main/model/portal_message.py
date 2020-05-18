import enum
from .. import db


class PortalMssgDirection(enum.Enum):
    # Client authored message
    INBOUND = 'inbound'
    # Rep authored message
    OUTBOUND = 'outbound'


class PortalMessage(db.Model):
    """ Represents a Portal message """
    __tablename__ = 'portal_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime)

    content = db.Column(db.String(918))
    direction = db.Column(db.String(20))
    author_id = db.Column(db.Integer)
    author_name = db.Column(db.String(50)) 
    is_viewed = db.Column(db.Boolean, default=False)

    # Relationships
    portal_user_id = db.Column(db.Integer, db.ForeignKey('portal_users.id', name='fk_portal_messages_portal_users_id'), nullable=True)