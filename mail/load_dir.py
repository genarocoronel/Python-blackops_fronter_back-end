# Importing libraries for use
# Importing flask
from bottle import Bottle, request

######################
## Authents Imports ##
######################
from auth.auth import authenticate

#########################
## Mail Server Imports ##
#########################
from .mail import *

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

# Function for loading all of the paths for this project
def mail_load(app):
    @app.route('/mail/server/status', method='POST')
    def mailserver_status():
        return mail_server_status(request.body.read())

    @app.route('/mail/server/start', method='POST')
    def mailserver_start():
        return mail_server_start(request.body.read())

    @app.route('/mail/server/stop', method='POST')
    def mailserver_stop():
        return mail_server_stop(request.body.read())
    @app.route('/mail/send', method='POST')
    def sendmail():
        return send_mail(request.body.read())
