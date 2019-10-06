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
from .chat import *
from .channel import *

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

# Function for loading all of the paths for this project
def chat_load(app):
    @app.route('/chat/channel/get', method='POST')
    def channel_get():
        return get_channel(request.body.read())

    @app.route('/chat/channel/create', method='POST')
    def channel_add():
        return create_channel(request.body.read())

    @app.route('/chat/channel/edit', method='POST')
    def channel_edit():
        return edit_channel(request.body.read())

    @app.route('/chat/get', method='POST')
    def chat_get():
        return get_chat(request.body.read())

    @app.route('/chat/send', method='POST')
    def chat_send():
        return send_chat(request.body.read())

    @app.route('/chat/channel/get/members', method='POST')
    def get_members():
        return get_channel_members(request.body.read())

    @app.route('/chat/channel/edit_full', method='POST')
    def channel_edit_full():
        return edit_channel_full(request.body.read())