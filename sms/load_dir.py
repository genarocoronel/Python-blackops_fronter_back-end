# Importing libraries for use
# Importing flask
from bottle import Bottle, request

######################
## Authents Imports ##
######################
from auth.auth import authenticate

#########################
## Appointment Imports ##
#########################
from .sms import *

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

def sms_load(app):
    @app.route('/sms/get', method='POST')
    def get_sms():
        # Authenticating
        authenticate_default()

        return sms_get(request.body.read())

    @app.route('/sms/send', method='POST')
    def sms_send():
        # Authenticating
        authenticate_default()

        return sms_send_auth(request.body.read())

    @app.route('/sms/recieve', method='POST')
    def recieve_sms():
        # Authenticating
        authenticate_default()

        return sms_recieve(request.body.read())

    @app.route('/sms/template/get', method='POST')
    def get_template_sms():
        # Authenticating
        authenticate_default()

        return sms_template_get(request.body.read())

    @app.route('/sms/template/add', method='POST')
    def add_template_sms():
        # Authenticating
        authenticate_default()

        return sms_template_add(request.body.read())