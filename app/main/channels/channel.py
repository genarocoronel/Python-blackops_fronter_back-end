from flask_socketio import Namespace, emit
from app.main import wscomm
from flask import request
from app.main.core.auth import Auth
from flask import current_app as app

## base socketio/webocket wrapper
class Channel(Namespace):
    CHANNELS_STORAGE_EXPIRY = 3600

    def on_open(self, user):
        pass

    def on_close(self, user):
        pass

    def on_connect(self):
        if request.headers and 'Authorization' in request.headers:
            # find the user using the token
            token = request.headers['Authorization']
            user = Auth.get_user_from_token(token)
            if user:
                # storage id
                u_key = "channels:user:{}".format(user.id)
                # update the storage
                app.redis.set(u_key, request.sid, ex=self.CHANNELS_STORAGE_EXPIRY)
                # add the socket id into store
                self.on_open(user)
           
    def on_disconnect(self):
        if request.headers and 'token' in request.headers:
            # find the user using the token
            token = request.headers['token']
            user = Auth.get_user_from_token(token)
            if user:
                # storage id
                u_key = "channels:user:{}".format(user.id)
                self.on_close(user)
                # update the storage
                app.redis.delete(u_key)


    @staticmethod
    def send_event(user_id, event_type, event_params, namespace):
        u_key = "channels:user:{}".format(user_id)
        sid = app.redis.get(u_key) 
        if sid:
            emit(event_type, event_params, room=sid, namespace=namespace)


    @classmethod
    def register(cls, obj):
        wscomm.on_namespace(obj)


