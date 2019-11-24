import redis
import rq as rq
from flask import current_app
import datetime

from app.main import db


class ImportTask(db.Model):
    __tablename__ = "import_tasks"

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    message = db.Column(db.String(255), nullable=True)
    import_id = db.Column(db.Integer, db.ForeignKey('candidate_imports.id'))
    complete = db.Column(db.Boolean, default=False)

    @property
    def progress(self):
        return self.get_progress()

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


class ScrapeTask(db.Model):
    __tablename__ = "scrape_tasks"

    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    inserted_on = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    updated_on = db.Column(db.DateTime, nullable=True)
    complete = db.Column(db.Boolean, default=False)

    @property
    def progress(self):
        return self.get_progress()

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
