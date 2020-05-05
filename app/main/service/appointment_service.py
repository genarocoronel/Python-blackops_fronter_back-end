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


class AppointmentWorkflow(Workflow):
    _task_assign_type = TaskAssignType.AUTO
    _task_due = 24 ## task expiry in hours
    _task_priority = TaskPriority.MEDIUM
    _task_ref_type = 'Appointment'

    def __init__(self, appt):
        agent_id = appt.agent_id 
        client_id = appt.client_id
        super().__init__(appt, agent_id, client_id) 

    def on_missed(self):
        self._task_title = 'Missed Appointment'
        self._task_desc = 'Missed Appointment - Action Required'

        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.MISSED.name
            appt = self._object
            self.owner = appt.team_manager_id
            self._create_task()
            self.save()

    def on_incomplete(self):
        self._task_title = 'Incomplete Appointment'
        self._task_desc = 'Appointment marked Incomplete - Action Required'

        if self.status == AppointmentStatus.SCHEDULED.name:
            self.status = AppointmentStatus.INCOMPLETE.name
            appt = self._object
            self.owner = appt.agent_id 
            self._create_task()
            self.save()

class AppointmentService(object):
    allowed_roles = [RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP]
    #serializer_class = TeamDto.team_request
    
    @classmethod
    def get(cls, appt_id):
        appt = Appointment.query.filter_by(public_id=appt_id).first()
        return appt

    @classmethod
    def list(cls):
        appts = Appointment.query.all()        
        return appts

    @classmethod    
    def save(cls, request):
        data = request.json
        status = AppointmentStatus.SCHEDULED
        agent = get_request_user()
        note = data.get('note')
        client = Client.query.filter_by(public_id=data.get('client_id')).first()
        if not client:
            raise ValueError("Client not found")

        scheduled_date = dt_parse(data.get('scheduled_on'))
        appt = Appointment(public_id=str(uuid.uuid4()),
                           client_id=client.id,
                           agent_id=3,
                           scheduled_at=scheduled_date,
                           summary=data.get('summary'),
                           location=data.get('loc'),
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

            # update the workflow
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

     

