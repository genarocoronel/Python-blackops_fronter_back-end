from rq import Worker, Connection
from flask import current_app
from app.main.tasks import channel


def run_worker(queue):
    # initialize worker channel
    channel.WorkerChannel.init() 

    with Connection(current_app.redis):
        qs = [queue] or ['default']

        worker = Worker(qs)
        worker.work()
