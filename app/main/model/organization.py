from app.main import db


## Multi organization support
class Organization(db.Model):
    """ db for storing Organization details"""
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Elite DMS  
    name = db.Column(db.String(120), unique=True, nullable=False)
    url  = db.Column(db.String(200), unique=True, nullable=False)   

    # mobile application name
    app_name = db.Column(db.String(120), unique=True, nullable=False)
    # logo url
    logo_url = db.Column(db.String(200), unique=True, nullable=False)
    # client portal
    client_portal = db.Column(db.String(200), unique=True, nullable=False) 


