import enum

from flask import current_app

from app.main.model.task import ImportTask
from .. import db


class CandidateImportStatus(enum.Enum):
    CREATED = "created"  # waiting on task to be enqueued
    RECEIVED = "received"  # task has been enqueued
    RUNNING = "running"  # task is being executed and has not finished
    FINISHED = "finished"  # task completed successfully
    ERROR = "error"  # task finished with error


class CandidateImport(db.Model):
    """ Candidate Import Model for importing candidates from file upload """
    __tablename__ = "candidate_imports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file = db.Column(db.String(255), nullable=False)
    tasks = db.relationship('ImportTask', backref='candidate_import', lazy='dynamic')
    status = db.Column(db.Enum(CandidateImportStatus), nullable=False, default=CandidateImportStatus.CREATED)
    inserted_on = db.Column(db.DateTime, nullable=False)
    updated_on = db.Column(db.DateTime, nullable=False)

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.main.tasks.' + name, self.id, *args, **kwargs)
        task = ImportTask(id=rq_job.get_id(), name=name, description=description, candidate_import=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return ImportTask.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return ImportTask.query.filter_by(name=name, user=self, complete=False).first()
