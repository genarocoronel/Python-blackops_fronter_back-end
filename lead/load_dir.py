# Importing flask
from bottle import Bottle, request

######################
## Authents Imports ##
######################
from auth.auth import authenticate

#########################
## Appointment Imports ##
#########################
from .lead import *

def lead_load(app):
    @app.route('/lead/get', method='POST')
    def lead_get():
        return get_lead(request.body.read())

    @app.route('/lead/add', method='POST')
    def lead_add_single():
        return add_lead_single(request.body.read())

    @app.route('/lead/edit', method='POST')
    def lead_edit():
        return edit_lead(request.body.read())

    @app.route('/lead/load', method='POST')
    def lead_load_direct():
        return lead_load_direct(request.body.read())

    @app.route('/lead/load_id', method='POST')
    def lead_load_direct():
        return load_lead_from_init(request.body.read())