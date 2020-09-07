from flask import current_app as app


class Auditor():
    @classmethod
    def launch_task(cls, *args, **kwargs):
        """ Launches an Audit recording task """
        app.queue.enqueue('app.main.tasks.audit.record', failure_ttl=300, *args, **kwargs)
