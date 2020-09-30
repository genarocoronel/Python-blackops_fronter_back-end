import datetime
from datetime import timedelta
import uuid
from app.main.core.rac import RACRoles
from app.main import db
from app.main.model.appointment import Appointment, AppointmentStatus, AppointmentNote
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority
from dateutil.parser import parse as dt_parse
from app.main.channels.notification import TaskChannel
import app.main.service.workflow as workflow
from app.main.model.client import Client
from app.main.service.user_service import get_request_user
from app.main.model import Language
from flask import current_app as app


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
                wf = workflow.AppointmentWorkflow(appt)
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

     
