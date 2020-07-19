import argparse
import sys
import os

from redis import Redis
from rq_scheduler.scheduler import Scheduler
from rq_scheduler.utils import setup_loghandlers
from datetime import datetime

from flask import current_app as app

def register_jobs(scheduler):
    try:
        # schedule rsign status check
        # schedule every 2 minutes
        scheduler.cron('*/2 * * * *',
                        func='app.main.tasks.docusign.check_sessions',
                        args=[],
                        description='kron: check_sessions',
                        repeat=None)

        # schedule debt payment EFT
        # schedule at 8:00 PM everyday
        scheduler.cron('0 20 * * *',
                       func='app.main.tasks.debt_payment.process_debt_payments',
                       args=[],
                       description='kron: process_debt_payments',
                       repeat=None) 

        # every hour check the status of EFT 
        scheduler.cron('0 */4 * * *',
                       func='app.main.tasks.debt_payment.check_eft_status',
                       args=[],
                       description='kron: check_eft_status',
                       repeat=None)

        # every day 12 PM, send payment reminders
        scheduler.cron('0 20 * * *',
                       func='app.main.tasks.debt_payment.process_upcoming_payments',
                       args=[],
                       description='kron: process_upcoming_payments',
                       repeat=None)

    except Exception as err:
        app.logger.warning("Schudler Init issue {}".format(str(err)))


def scheduler_init():
    parser = argparse.ArgumentParser(description='Runs RQ scheduler')
    parser.add_argument('-b', '--burst', action='store_true', default=False, help='Run in burst mode (quit after all work is done)')
    parser.add_argument('-H', '--host', default=os.environ.get('RQ_REDIS_HOST', 'localhost'), help="Redis host")
    parser.add_argument('-p', '--port', default=int(os.environ.get('RQ_REDIS_PORT', 6379)), type=int, help="Redis port number")
    parser.add_argument('-d', '--db', default=int(os.environ.get('RQ_REDIS_DB', 0)), type=int, help="Redis database")
    parser.add_argument('-P', '--password', default=os.environ.get('RQ_REDIS_PASSWORD'), help="Redis password")
    parser.add_argument('--verbose', '-v', action='store_true', default=False, help='Show more output')
    parser.add_argument('--quiet', action='store_true', default=False, help='Show less output')
    parser.add_argument('--url', '-u', default=os.environ.get('RQ_REDIS_URL')
        , help='URL describing Redis connection details. \
            Overrides other connection arguments if supplied.')
    parser.add_argument('-i', '--interval', default=60.0, type=float
        , help="How often the scheduler checks for new jobs to add to the \
            queue (in seconds, can be floating-point for more precision).")
    parser.add_argument('--path', default='.', help='Specify the import path.')
    parser.add_argument('--pid', help='A filename to use for the PID file.', metavar='FILE')
    parser.add_argument('-j', '--job-class', help='Custom RQ Job class')
    parser.add_argument('-q', '--queue-class', help='Custom RQ Queue class')

    args = parser.parse_args()

    if args.path:
        sys.path = args.path.split(':') + sys.path

    if args.pid:
        pid = str(os.getpid())
        filename = args.pid
        with open(filename, 'w') as f:
            f.write(pid)

   
    if args.url is not None:
        connection = Redis.from_url(args.url)
    else:
        connection = Redis(args.host, args.port, args.db, args.password)

    if args.verbose:
        level = 'DEBUG'
    elif args.quiet:
        level = 'WARNING'
    else:
        level = 'INFO'
    setup_loghandlers(level)

    scheduler = Scheduler('default', 
                          connection=connection)
    jobs = scheduler.get_jobs()
    for job in jobs:
        # print(job.description)
        # if schedule or cron jobs, delete it
        if 'kron:' in job.description:
            job.delete()

    # register the jobs
    register_jobs(scheduler)
    scheduler.run(burst=args.burst)

if __name__ == '__main__':
    scheduler_init()
