# Importing flask
from bottle import Bottle, request

######################
## Authents Imports ##
######################
from auth.auth import authenticate

#########################
## Appointment Imports ##
#########################
from .voip import *

def voip_load(app):
    @app.route('/voip/route', method='POST')
    def route_voip():
        return voip_route(request.body.read())

    @app.route('/voip/recieve', method='POST')
    def inbound_voip():
        return voip_inbound(request.body.read())

    @app.route('/voip/status_callback', method='POST')
    def status_callback():
        return voip_status_callback(request.body.read())