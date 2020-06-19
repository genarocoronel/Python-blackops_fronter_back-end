from flask import request
from flask import current_app as app
import enum
from .channel import Channel
from .serializer import serialize
from app.main.util.dto import TeamDto, TaskDto, ClientDto


class NotificationType(enum.Enum):
    TASK = 'task'
    TEAMREQUEST = 'team_request'
    CLIENT_NOTICE = 'client_notice'

## this channel is used to send real time announcements
## to user dashboards
class NotificationChannel(Channel):
    namespace = '/notify'
    _tx_chnl = Channel

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
    @serialize
    def send(cls, user_id, data): 
        try:
            if not isinstance(cls.type, NotificationType):
                return False

            # notification type
            event_type = cls.type.value
            ns = cls.namespace 

            # send through transmit channel
            cls._tx_chnl.send_event(user_id, 
                                    event_type, 
                                    data,
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

## Notification multiplexing
## for new types - add here

# team request notification
class TeamRequestChannel(NotificationChannel):
    type = NotificationType.TEAMREQUEST
    serializer_class = TeamDto.team_request

## User task notification
class TaskChannel(NotificationChannel):
    type = NotificationType.TASK
    serializer_class = TaskDto.user_task

## client assigned notice
class ClientNoticeChannel(NotificationChannel):
    type = NotificationType.CLIENT_NOTICE
    serializer_class = ClientDto.client_notice


# register the channel
NotificationChannel.register()
        
