from app.main.model.appointment import Appointment, AppointmentStatus
from datetime import datetime, timedelta
from app.main.tasks.mailer import send_hour1_appointment_reminder, send_day1_appointment_reminder
from sqlalchemy import and_


def process_scheduled_appointments():

    current_dt = datetime.utcnow() 
    # if appointment status is not updated after 60 mins
    # change status to missed 
    limit_dt = current_dt - timedelta(hours=60)

    # fetch all the scheduled appointments 
    appointments = Appointment.query.filter_by(status=AppointmentStatus.SCHEDULED.name).all()
    for appt in appointments:
        schd_dt = appt.scheduled_at     

        if schd_dt < limit_dt:
            appt.status = AppointmentStatus.MISSED.name
            # add task to the manager 

        db.session.commit()
        


def trigger_appointment_reminders():
    """
    Trigger appointment reminders
    1H Appointment reminder  -- sends 1H prior to appointment 
    1D Appointment reminder  -- sends 24H prior to appointment
    """
    current_time = datetime.now().replace(second=0, microsecond=0)
    start = current_time + timedelta(minutes=60)
    end = start + timedelta(minutes=5)
    start = start - timedelta(minutes=5) 
    # 1H payment reminder
    appointments = Appointment.query.filter(and_(Appointment.status==AppointmentStatus.SCHEDULED.name, 
                                                 Appointment.scheduled_at >= start,
                                                 Appointment.scheduled_at <= end)).all()
    for appointment in appointments:
        client = appointment.client
        reminder_status = appointment.reminder_status
        if reminder_status['h1'] is False:
            # send 1H payment reminder notice
            send_hour1_appointment_reminder(client.id,
                                            appointment.id)
            reminder_status['h1'] = True
            appointment.reminder_status = reminder_status
            db.session.commit()

    # 24H payment reminder
    start = current_time + timedelta(days=1)
    end   = start + timedelta(minutes=5)     
    start = start - timedelta(minutes=5) 
    appointments = Appointment.query.filter(and_(Appointment.status==AppointmentStatus.SCHEDULED.name,
                                                 Appointment.scheduled_at >= start,
                                                 Appointment.scheduled_at <= end)).all()    
    for appointment in appointments:
        client = appointment.client
        reminder_status = appointment.reminder_status
        if reminder_status['d1'] is False:
            # send 1D payment reminder notice
            send_day1_appointment_reminder(client.id,
                                           appointment.id)
            reminder_status['d1'] = True
            appointment.reminder_status = reminder_status
            db.session.commit()

