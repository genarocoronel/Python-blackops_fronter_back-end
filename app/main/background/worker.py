from rq import Worker, Connection
from flask import current_app


def run_worker(queue):
    with Connection(current_app.redis):
        qs = [queue] or ['default']

        worker = Worker(qs)
        worker.work()
