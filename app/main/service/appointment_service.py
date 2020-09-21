import datetime
from datetime import timedelta
import uuid
from app.main.core.rac import RACRoles
from app.main import db
from app.main.model.appointment import Appointment, AppointmentStatus, AppointmentNote
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority
from dateutil.parser import parse as dt_parse
from app.main.channels.notification import TaskChannel
from app.main.service.workflow import Workflow
from app.main.model.client import Client
from app.main.service.user_service import get_request_user
from app.main.model import Language
from flask import current_app as app


class AppointmentWorkflow(Workflow):
    _task_assign_type = TaskAssignType.AUTO
    _task_due = 24 ## task expiry in hours
    _task_priority = TaskPriority.MEDIUM
    _task_ref_type = 'Appointment'

    def __init__(self, appt):
        agent_id = appt.agent_id 
        client_id = appt.client_id
        super().__init__(appt, agent_id, client_id) 

    def _update_service_schedule(self, status):
        appt = self._object
        if appt.service_schedule:
            svc_schedule = appt.service_schedule
            svc_schedule.status = status
            svc_schedule.updated_on = datetime.utcnow()
            svc_schedule.updated_by_username = 'system'
            db.session.commit()

    def on_missed(self):
        self._task_title = 'Missed Appointment'
        self._task_desc = 'Missed Appointment - Action Required'

        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.MISSED.name
            self._update_service_schedule(ServiceScheduleStatus.INCOMPLETE.value)
            appt = self._object
                
            # TODO find the manager
            self._create_task()
            self.save()

             

    def on_incomplete(self):
        self._task_title = 'Incomplete Appointment'
        self._task_desc = 'Appointment marked Incomplete - Action Required'

        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.INCOMPLETE.name
            self._update_service_schedule(ServiceScheduleStatus.INCOMPLETE.value)
            appt = self._object
            self.owner = appt.agent_id 
            self._create_task()
            self.save()

    def on_completed(self):
        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.COMPLETED.name 
            self._update_service_schedule(ServiceScheduleStatus.COMPLETE.value)
            self.save()

            appt = self._object
            client = appt.client
            if client.language == Language.SPANISH.name:
                app.queue.enqueue('app.main.tasks.mailer.send_spanish_general_call',  # task routine
                                  client.id, # client id
                                  failure_ttl=300)
            else:
                app.queue.enqueue('app.main.tasks.mailer.send_general_call_edms',  # task routine
                                  client.id, # client id
                                  failure_ttl=300)

class AppointmentService(object):
    
    @classmethod
    def get(cls, appt_id):
        appt = Appointment.query.filter_by(public_id=appt_id).first()
        return appt

    @classmethod
    def list(cls):
        user = get_request_user()
        agents = [ user ]
        # TODO Manager view
        userids = [user.id for user in agents]
        appts = Appointment.query.filter(Appointment.agent_id.in_(userids)).all()        
        print(appts)
        return appts

    @classmethod
    def save(cls, request):
        try:
            data = request.json
            status = AppointmentStatus.SCHEDULED
            # fetch the account_manager for the client

            note = data.get('note')
            client = Client.query.filter_by(friendly_id=data.get('client')['friendly_id']).first()
            if not client:
                raise ValueError('Client not exist')
            # assign to the service user in client file.
            agent_id = client.account_manager_id

            appt = Appointment(public_id=str(uuid.uuid4()),
                               client_id=client.id,
                               agent_id=agent_id,
                               scheduled_at=data.get('scheduled_at'),
                               summary=data.get('summary'),
                               loc_time_zone=data.get('loc_time_zone'),
                               status=status.name,
                               reminder_types=data.get('reminder_types'),)
            db.session.add(appt)
            db.session.commit()

            # add a note 
            if note and note.strip() != '':
                appt_note = AppointmentNote(author_id=data.get('employee_id'),
                                            appointment_id=appt.id,
                                            content=note)
                db.session.add(appt_note)
        except Exception as err:
            raise ValueError("New Appointment failed: {}".format(str(err)))

        return appt

    @classmethod
    def update(cls, appt_id, request):
        try:
            data = request.json
            status = data.get('status')
            note = data.get('note')
                              
            appt = Appointment.query.filter_by(public_id=appt_id).first()
            if not appt:
                raise ValueError("Appointment not found")

            client = Client.query.filter_by(public_id=data.get('client')['public_id']).first()
            # update the workflow
            for attr in data:
                if hasattr(appt, attr):
                    if attr == 'client':
                        setattr(appt, 'client_id', client.id)
                    elif attr == 'agent':
                        print("attr")
                    else:
                        setattr(appt, attr, data.get(attr))
            # change the status  
            if status and status in AppointmentStatus.__members__:
                handler = "on_{}".format(status.lower())
                wf = AppointmentWorkflow(appt)
                func = getattr(wf, handler, None)
                if func: 
                    func()     
                
            # add a note 
            if note and note.strip() != '':
                # access from the request
                agent_id = appt.agent_id
                appt_note = AppointmentNote(author_id=agent_id,
                                            appointment_id=appt.id,
                                            content=note)
                db.session.add(appt_note)

            # update the modified time
            appt.modified_date = datetime.datetime.utcnow()
            db.session.commit()

        except Exception as err:
            raise ValueError("Appointment Update failed {}".format(str(err)))

        return appt

     
