# Importing libraries for use
# Importing flask
from bottle import Bottle, request

######################
## Authents Imports ##
######################
from auth.auth import authenticate

######################
## Employee Imports ##
######################
from .call import *

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

def call_load(app):
    @app.route('/call/get', method='POST')
    def call_gets():
        # Authenticating
        authenticate_default()

        # Loading the login with the post data
        return get_calls(request.body.read())