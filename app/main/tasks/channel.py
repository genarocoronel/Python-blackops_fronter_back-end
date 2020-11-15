from redis import Redis
from app.main.background import worker
from flask import current_app as app
from flask_socketio import SocketIO

# worker socketio
sockio = None
sid_store = None


class WorkerChannel(object):

    @staticmethod
    def init():
        # socketio
        global sockio
        global sid_store

        sockio = SocketIO(message_queue=app.config['REDIS_URL'],
                          path='/channels',)
        # sid store
        sid_store = Redis.from_url(app.config['REDIS_URL'],
                                   charset="utf-8",
                                   decode_responses=True)

    @staticmethod
    def send_event(user_id, event_type, event_params, namespace):
        app.logger.info("Worker channel Send {}".format(event_type))

        if sockio is None:
            # error
            app.logger.warning("Worker channel is not initialized")
            return

        # fetch room-id for userid
        u_key = "channels:user:{}".format(user_id)
        sid = sid_store.get(u_key)
        if sid:
            sockio.emit(event_type, 
                        event_params,
                        room=sid,
                        namespace=namespace)
           
    @staticmethod
    def broadcast_event(event_type, event_params, namespace):
        app.logger.info("Worker channel Send {}".format(event_type))

        if sockio is None:
            # error
            app.logger.warning("Worker channel is not initialized")
            return

        sockio.emit(event_type, 
                    event_params,
                    namespace=namespace,
                    broadcast=True)


class ClientUpdateNotice(object):
    
    def __init__(self, client, msg=None):
        self._public_id = client.public_id
        self._friendly_id = client.friendly_id
        if msg is None:
            self._msg = 'Client file updated'
        else:
            self._msg = msg
        self._client_type = client.type.value

    @property
    def public_id(self):
        return self._public_id

    @property
    def friendly_id(self):
        return self._friendly_id

    @property
    def client_type(self):
        return self._client_type

    @property
    def msg(self):
        return self._msg


# worker channels
from app.main.channels import notification 

class WkTaskChannel(notification.TaskChannel):
    _tx_chnl = WorkerChannel

class WkClientNoticeChannel(notification.ClientNoticeChannel):
    _tx_chnl = WorkerChannel

class WkCientUpdateChannel(notification.ClientUpdateChannel):
    _tx_chnl = WorkerChannel

