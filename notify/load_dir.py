# Importing libraries for use
# Importing flask
from bottle import Bottle, request

######################
## Authents Imports ##
######################
from auth.auth import authenticate

#########################
## Chttng/Chnl Imports ##
#########################
from .notify import *

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

# Function for loading all of the paths for this project
def notify_load(app):
    print("Loading notifications")

    @app.route('/notify/get', method='POST')
    def notify_get():
        # Authenticating
        authenticate_default()

        return get_notify(request.body.read())

    @app.route('/notify/add', method='POST')
    def notify_get():
        # Authenticating
        authenticate_default()

        return add_notify(request.body.read())

    @app.route('/notify/view', method='POST')
    def notify_get():
        # Authenticating
        authenticate_default()

        return view_notify(request.body.read())