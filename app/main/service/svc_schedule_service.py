import uuid
import datetime

from app.main.core.errors import NotFoundError, NoDuplicateAllowed, BadRequestError
from app.main import db
from app.main.model.service_schedule import ServiceSchedule, ServiceScheduleStatus, ServiceScheduleType
from app.main.model.appointment import Appointment, AppointmentType
import app.main.service.workflow as workflow
from flask import current_app as app
from flask import g


def create_svc_schedule(client, term_months = 24):
    """ Creates the initial Service Schedule for a Client """
    # Note: Per DKW on 20 Jul 2020 - generated automatically out to 48 months for every client upon signing
    svc_schedule_records = ServiceSchedule.query.filter_by(client_id=client.id).order_by(db.asc(ServiceSchedule.id)).all()
    if not svc_schedule_records:
        app.logger.info(f'Client does not have Service Schedule and needs to be created.')
        svc_schedule_records = _generate_svc_schedule(client, term_months)
        
    return _synth_schedule(svc_schedule_records)


def get_svc_schedule(client):
    """ Gets a Service Schedule for a Client """
    svc_schedule = []

    app.logger.info(f"Getting service schedule for Client with ID {client.public_id}")
    svc_schedule_records = ServiceSchedule.query.filter_by(client_id=client.id).order_by(db.asc(ServiceSchedule.id)).all()

    if svc_schedule_records:
        svc_schedule = _synth_schedule(svc_schedule_records)

    return svc_schedule


def update_svc_schedule(client, schedule_data):
    """ Updates the Service Schedule for a given Client """
    updated_items = []
    for sched_data_item in schedule_data:
        is_updated = False
        if 'public_id' not in sched_data_item:
            raise BadRequestError("'public_id' for a service schedule item is missing. Please correct this and try again")

        sched_item_record = ServiceSchedule.query.filter_by(public_id=sched_data_item['public_id']).first()
        if not sched_item_record:
            raise BadRequestError(f"Scheduled item not found for ID {sched_data_item['public_id']}")

        if client.id is not sched_item_record.client_id:
            raise BadRequestError(f"Cannot update this schedule item with public ID {sched_item_record.public_id} as it doesn't belong to this Client")
        
        # re-schedule not allowed for AUTO TXT 
        if ServiceScheduleType.TEXT.value in sched_item_record.type: 
            raise BadRequestError(f"Re-Schedule not allowed for AUTO Service TXT {sched_data_item['public_id']}") 

        if 'scheduled_for' in sched_data_item and sched_data_item['scheduled_for']:
            if sched_item_record.scheduled_for:
                sched_item_record.tot_reschedule = sched_item_record.tot_reschedule + 1
            
            tmp_datetime = datetime.datetime.strptime(sched_data_item['scheduled_for'], '%Y-%m-%dT%H:%M:%S.%fZ')
            sched_item_record.scheduled_for = tmp_datetime

            # service calls should be appointments
            if ServiceScheduleType.CALL.value in sched_item_record.type:
                # check the related appointment
                appointment = sched_item_record.appointment
                if appointment:
                    # modified the appointment time
                    appointment.scheduled_at = tmp_datetime
                else:
                    # create an appointment
                    appointment =  Appointment(public_id=str(uuid.uuid4()),
                                               client_id=client.id,
                                               agent_id=client.account_manager_id,
                                               scheduled_at=tmp_datetime,
                                               summary=sched_item_record.type,
                                               type=AppointmentType.SERVICE_CALL.name)  
                    save_changes(appointment)
                    sched_item_record.appointment_id = appointment.id
            # updated
            is_updated = True
        
        if 'status' in sched_data_item and sched_data_item['status']:
            if not ServiceScheduleStatus.is_valid_status(sched_data_item['status']):
                    raise BadRequestError(f"The given status {sched_data_item['status']} is invalid. Allowed are: pending, complete, incomplete, rescheduled")

            sched_item_record.status = sched_data_item['status']
            is_updated = True

            # TODO trigger apointment SM
            if ServiceScheduleType.CALL.value in sched_item_record.type:
                appointment = sched_item_record.appointment
                if appointment:
                    wflow = workflow.AppointmentWorkflow(appointment) 
                    handler = "on_ss_{}".format(sched_data_item['status'])
                    func = getattr(wflow, handler, None)
                    if func:
                        func()

        if is_updated:
            sched_item_record.updated_on = datetime.datetime.utcnow()
            sched_item_record.updated_by_username = g.current_user['username']
            save_changes(sched_item_record)
            updated_items.append(sched_item_record)


    return _synth_schedule(updated_items)
        

def _generate_svc_schedule(client, term):
    """ Generates initial Service Schedule for a Client """

    svc_schedule = _generate_boilerplate_svc_schedule(client)

    sched_item_num = 1011
    months_remaining = term - 3
    app.logger.info(f'This many term months remaining {months_remaining}')
    call_starting_days_out = 90
    pull_starting_days_out = 105

    for i in range (months_remaining):
        call_starting_days_out = call_starting_days_out + 30
        sched_item_num = sched_item_num + 1
        tmp_call = f'{call_starting_days_out} Day Call'
        app.logger.info(f"Creating: {tmp_call}")
        tmp_call_item = ServiceSchedule(
            public_id = str(uuid.uuid4()),
            schedule_item = sched_item_num,
            type = tmp_call,
            client_id = client.id,
            inserted_on = datetime.datetime.utcnow(),
            updated_on = datetime.datetime.utcnow(),
            updated_by_username = 'system'
        )
        db.session.add(tmp_call_item)
        svc_schedule.append(tmp_call_item)

        pull_starting_days_out = pull_starting_days_out + 30
        sched_item_num = sched_item_num + 1
        tmp_credit_pull = f'{pull_starting_days_out} Credit Pull'
        app.logger.info(f"Creating: {tmp_credit_pull}")
        tmp_sc_pull_item = ServiceSchedule(
            public_id = str(uuid.uuid4()),
            schedule_item = sched_item_num,
            type = tmp_credit_pull,
            client_id = client.id,
            inserted_on = datetime.datetime.utcnow(),
            updated_on = datetime.datetime.utcnow(),
            updated_by_username = 'system'
        )
        db.session.add(tmp_sc_pull_item)
        svc_schedule.append(tmp_sc_pull_item)

    save_changes()
    
    return svc_schedule


def _generate_boilerplate_svc_schedule(client):
    """ Generates the Boilerplate Service Schedule """
    boilerplate_sched = []

    svc_sched1001 = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1001,
        type = 'Introduction Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1001)
    boilerplate_sched.append(svc_sched1001)

    # 3 DAY Text - Auto
    dt3 = datetime.datetime.utcnow() + datetime.timedelta(days=3)
    # 12 Noon
    dt3 = dt3.replace(hour=12, minute=0, second=0, microsecond=0)
    svc_sched1002  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1002,
        type = '3 Day Text',
        status = ServiceScheduleStatus.PENDING.value,
        scheduled_for=dt3,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1002)
    boilerplate_sched.append(svc_sched1002)

    svc_sched1003  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1003,
        type = '7 Day Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1003)
    boilerplate_sched.append(svc_sched1003)

    svc_sched1004  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1004,
        type = '15 Day Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1004)
    boilerplate_sched.append(svc_sched1004)

    svc_sched1005  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1005,
        type = '30 Day Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1005)
    boilerplate_sched.append(svc_sched1005)

    svc_sched1006  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1006,
        type = '45 Day Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1006)
    boilerplate_sched.append(svc_sched1006)

    svc_sched1007  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1007,
        type = '60 Day Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1007)
    boilerplate_sched.append(svc_sched1007)

    svc_sched1008  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1008,
        type = '75 Day Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1008)
    boilerplate_sched.append(svc_sched1008)

    svc_sched1009  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1009,
        type = '75 Credit Pull',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1009)
    boilerplate_sched.append(svc_sched1009)

    svc_sched1010  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1010,
        type = '90 Day Call',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1010)
    boilerplate_sched.append(svc_sched1010)

    svc_sched1011  = ServiceSchedule(
        public_id = str(uuid.uuid4()),
        schedule_item = 1011,
        type = '105 Day Credit Pull',
        status = ServiceScheduleStatus.PENDING.value,
        client_id = client.id,
        inserted_on = datetime.datetime.utcnow(),
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = 'system'
    )
    db.session.add(svc_sched1011)
    boilerplate_sched.append(svc_sched1011)

    return boilerplate_sched


def _synth_schedule(schedule):
    synth_sched = []
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'

    for sched_item in schedule:
        sched_for = None
        if sched_item.scheduled_for:
            sched_for = sched_item.scheduled_for.strftime(datetime_format)

        tmp_item = {
            'public_id': sched_item.public_id,
            'schedule_item': sched_item.schedule_item,
            'type': sched_item.type,
            'status': sched_item.status,
            'scheduled_for': sched_for,
            'tot_reschedule': sched_item.tot_reschedule,
            'inserted_on': sched_item.inserted_on.strftime(datetime_format),
            'updated_on': sched_item.updated_on.strftime(datetime_format),
            'updated_by_username': sched_item.updated_by_username,
        }
        synth_sched.append(tmp_item)

    return synth_sched


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()
