import datetime
from datetime import timedelta
import uuid
from app.main.core.rac import RACRoles
from app.main import db
from app.main.model.appointment import Appointment, AppointmentStatus
from app.main.model.usertask import UserTask, TaskAssignType, TaskPriority



class AppointmentWorkflow(object):
    _task_assign_type = TaskAssignType.AUTO
    _task_due = 24 ## task expiry in hours
    _task_priority = TaskPriority.MEDIUM

    def __init__(self, appt):
        self._appt = appt

    @property
    def status(self):
        status = AppointmentStatus[self._appt.status]
        return status

    def _create_task(self, owner, client, title, desc):
        due = datetime.datetime.utcnow() + timedelta(hours=self._task_due)
        task = UserTask(assign_type=self._task_assign_type,
                        owner_id=owner.id,                         
                        priority=self._task_priority,
                        title=title,
                        description=desc,
                        due_date=due,
                        client_id=client.id,
                        object_type='Appointment',
                        object_id=self._appt.id) 

        db.session.add(task)
        db.session.commit()
        TaskChannel.send(owner_id,
                         task)

    def on_missed(self):
        if self.status == AppointmentStatus.SCHEDULED:
            mgr = self._appt.team_manager
            # create a task 
            self._create_task(mgr,
                              self._appt.client,
                              'Missed Appointment',
                              '')

    def on_incomplete(self):
        if self.status == AppointmentStatus.SCHEDULED:
            # create a task
            self._create_task(mgr,
                              self._appt.client,
                              'Incomplete Appointment',
                              '')
         

class AppointmentService(object):
    allowed_roles = [RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP]
    #serializer_class = TeamDto.team_request
    
    @classmethod
    def get(cls, appt_id):
        appt = Appointment.query.filter_by(public_id=appt_id).first()
        return appt

    @classmethod
    def list(cls, self):
        appts = Appointment.query.all()        
        return appts

    @classmethod    
    def save(cls, request):
        data = request.json
        status = AppointmentStatus.SCHEDULED
        scheduled_date = datetime.datetime.strptime(data['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')    
        appt = Appointment(public_id=str(uuid.uuid4()),
                           client_id=data['client_id'],
                           agent_id=data['employee_id'],
                           scheduled_at=scheduled_date,
                           summary=data['summary'],
                           status=status.name,
                           reminder_types=data['reminder_types'],)
        db.session.add(appt)
        db.session.commit()

        return appt 

    @classmethod
    def update(cls, appt_id, request):
        data = request.json
        status = request.data.get('status')
        note = request.data.get('note')
                          
        appt = Appointment.query.filter_by(public_id=appt_id).first()
        if not appt:
            raise ValueError("Appointment not found")

        # update the workflow
        # change the status  
        if status and status in AppointmentStatus.__members__:
            handler = "on_{}".format(status)
            wf = AppointmentWorkflow(appt)
            func = getattr(wf, handler, None)
            if func: 
                func()     
            
        # add a note 
        if note and note.strip() != '':
            appt_note = AppointmentNote(author_id=agent_id,
                                        appointment_id=appt.id,
                                        content=note)
            db.session.add(appt_note)

        # update the modified time
        appt.modified_date = datetime.datetime.utcnow()
        db.session.commit()

        return appt

     

