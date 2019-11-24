from flask import current_app

from app.main import db


class Campaign(db.Model):
    """ Campaign Model """
    __tablename__ = 'campaigns'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), unique=True)
    inserted_on = db.Column(db.DateTime, nullable=False)

    # relationships
    candidates = db.relationship('Candidate', back_populates='campaign', lazy='dynamic')

    # fields
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(25), nullable=False)
    job_number = db.Column(db.String(25), unique=True, nullable=False)
    mailing_date = db.Column(db.String(10), nullable=False)
    offer_expire_date = db.Column(db.String(10), nullable=False)
    mailer_file = db.Column(db.String(100), unique=True, nullable=True)

    def launch_task(self, name, *args, **kwargs):
        current_app.mailer_file_queue.enqueue('app.main.tasks.campaign.' + name, self.id, *args, **kwargs)
