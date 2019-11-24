# Basic imports
import json
from bottle import Bottle, request

# Importing the phone
from .phone import *

######################
## Authents Imports ##
######################
from auth.auth import authenticate

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

# Config
from config.mysql_init import init_mysql

def phone_load(app):
    @app.route('/phone/inbound_route', method='POST')
    def inbound_phone():
        authenticate_default()

        phone_route_inbound(request.body.read())
