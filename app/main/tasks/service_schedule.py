from app.main.model.service_schedule import ServiceSchedule, ServiceScheduleStatus, ServiceScheduleType
from app.main.model.usertask import UserTask
from app.main.tasks.mailer import send_day3_reminder
from app.main.tasks import channel as wkchannel
from datetime import datetime, timedelta, date
from sqlalchemy import and_, func
from app.main import db


def process_service_schedules():
    dt_now = datetime.utcnow()
    
    ## TXT APPTS 
    schedules = ServiceSchedule.query.filter(and_(ServiceSchedule.status==ServiceScheduleStatus.PENDING.value,
                                                  ServiceSchedule.type.ilike('3 Day Text'),
                                                  func.date(ServiceSchedule.scheduled_for) == date.today())).all()
    for schedule in schedules:
        client = schedule.client
        # send sms text
        send_day3_reminder(client.id)
        # change the service schedule status
        schedule.status = ServiceScheduleStatus.COMPLETE.value
    db.session.commit()

    ## CREDIT PULL
    # create a task 5 days before the service call  
    dt_start = datetime.utcnow() 
    schedules = ServiceSchedule.query.filter(and_(ServiceSchedule.status==ServiceScheduleStatus.PENDING.value,
                                                  ServiceSchedule.type.contains(ServiceScheduleType.CREDIT_PULL.value),
                                                  func.date(ServiceSchedule.scheduled_for) == dt_start.date())).all()

    task_due = datetime.utcnow() + timedelta(hours=6)
    for schedule in schedules:
        client = schedule.client
        # account manager is not assigned
        if client.account_manager is None:
            continue

        # create a task for the account manager
        task = UserTask(title='Credit Pull',
                        description=schedule.type, 
                        due_date=task_due.replace(minute=0, second=0, microsecond=0),
                        client_id=client.id,
                        owner_id=client.account_manager_id,
                        object_type='ServiceSchedule',
                        object_id=schedule.id)
        db.session.add(task)
        db.session.commit()
        # notify the client
        wkchannel.WkTaskChannel.send(client.account_manager_id,
                                     task)
                        
                        
        
