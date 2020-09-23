from app.main.model.appointment import Appointment, AppointmentStatus, AppointmentType
from datetime import datetime, timedelta
from app.main.tasks.mailer import send_hour1_appointment_reminder, send_day1_appointment_reminder, send_day3_reminder 
from sqlalchemy import and_
from app.main import db


"""
Check for missed appointments
"""
def process_scheduled_appointments():
    dt_now = datetime.utcnow().replace(second=0, microsecond=0) 
    
    ## APPT REMINDERS
    # 1H Reminder
    start = dt_now + timedelta(minutes=60)
    end = start + timedelta(minutes=1)
    appointments = Appointment.query.filter(and_(Appointment.status==AppointmentStatus.SCHEDULED.name,
                                                 Appointment.type==AppointmentType.SERVICE_CALL.name,
                                                 Appointment.scheduled_at >= start,
                                                 Appointment.scheduled_at < end)).all()
    for appointment in appointments:
        client = appointment.client
        # send 1H payment reminder notice
        send_hour1_appointment_reminder(client.id,
                                        appointment.id)
    # 1D Reminder
    start = dt_now + timedelta(days=1)
    end   = start + timedelta(minutes=1)
    appointments = Appointment.query.filter(and_(Appointment.status==AppointmentStatus.SCHEDULED.name,
                                                 Appointment.type==AppointmentType.SERVICE_CALL.name,
                                                 Appointment.scheduled_at >= start,
                                                 Appointment.scheduled_at < end)).all() 
    for appointment in appointments:
        client = appointment.client
        # send 1D payment reminder notice
        send_day1_appointment_reminder(client.id,
                                       appointment.id)


    ## MISSED APPTS
    # if appointment status is not updated after 60 mins
    # change status to missed 
    dt_offset = dt_now - timedelta(minutes=60)
    # fetch all the missed appointments 
    appointments = Appointment.query\
                              .filter(and_(Appointment.status==AppointmentStatus.SCHEDULED.name, 
                                           Appointment.scheduled_at < dt_offset)).all()
    for appt in appointments:
        appt.status = AppointmentStatus.MISSED.name
        # TO: add task to the manager 
    db.session.commit()
        
