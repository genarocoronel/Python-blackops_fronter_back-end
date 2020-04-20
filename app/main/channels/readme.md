# Module

channels -- A light weight wrapper built using flask-socketio library.

# Deployment

The application uses python eventlet framework for deploying the application. The advantage of
eventlet is that it has websocket support unlike gevent.  

The applictaion is launched using following script,

```
python manage.py run
```

The production deployment logic will be implemented later using gunicorn or uWsgi server.

# Example

if you want to add a new channel, Please check ``` NotificationChannel ``` class in ``` notification.py ``` file.
