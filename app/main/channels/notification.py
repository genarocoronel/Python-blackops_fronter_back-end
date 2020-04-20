from flask import request
from flask import current_app as app
from flask_restplus import marshal
import enum
from .channel import Channel
from app.main.util.dto import TeamDto, TaskDto


class NotificationType(enum.Enum):
    TASK = 'task'
    TEAMREQUEST = 'team_request'


## this channel is used to send real time announcements
## to user dashboards
class NotificationChannel(Channel):
    namespace = '/notify'

    # Call back when a channel is opened
    def on_open(self, user):
        app.logger.info("Notification channel opened for userid({})".format(user.id))
    # call back when a channel is closed
    def on_close(self, user):
        app.logger.info("Notification channel closed for userid({})".format(user.id))
    # call back when a message is available
    def on_message(self, message):
        pass
    # send a message to a user 
    @classmethod
    def send_message(cls, user_id, ntype, data): 
        try:
            if not isinstance(ntype, NotificationType):
                return False

            event_params = {}
            # notification type
            event_type = ntype.value
            if ntype == NotificationType.TEAMREQUEST:
                event_params = marshal(data, TeamDto.team_request) 
            elif ntype == NotificationType.TASK:
                event_params = marshal(data, TaskDto.user_task)

            ns = cls.namespace 
            Channel.send_event(user_id, 
                               event_type, 
                               event_params,
                               namespace=ns)
            return True

        except Exception as err:
            app.logger.warning("Notification Channel send_message {}".format(str(err)))
            return False

    ## register name space
    @classmethod
    def register(cls):
        ns = cls.namespace
        Channel.register(cls(ns))

# register the channel
NotificationChannel.register()
        
