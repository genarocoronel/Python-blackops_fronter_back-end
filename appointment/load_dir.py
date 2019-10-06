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
from .appointment import *

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

# Function for loading all of the paths for this project
def appointment_load(app):

    @app.route('/appointment/add', method='POST')
    def appointment_add():
        # Authenticating
        authenticate_default()

        return add_appointment(request.body.read())

    @app.route('/appointment/get', method='POST')
    def appointment_get():
        # Authenticating
        authenticate_default()

        return get_appointment(request.body.read())

    @app.route('/appointment/edit', method='POST')
    def appointment_get():
        # Authenticating
        authenticate_default()

        return edit_appointment(request.body.read())
