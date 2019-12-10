import datetime

from flask import current_app
from rq import get_current_job
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from app.main import db
from app.main.model.credit_report_account import CreditReportAccount
from app.main.model.task import ScrapeTask
from app.main.scrape.crawl.spiders.credit_report_spider import CreditReportSpider


def _set_task_progress(progress, message=''):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
    job.save_meta()
    task = ScrapeTask.query.get(job.get_id())
    task.updated_on = datetime.datetime.utcnow()

    if progress >= 100:
        task.complete = True
        job.meta['message'] = message

    db.session.commit()


def _crawl_credit_report(account_id, username, password):
    process = CrawlerProcess(get_project_settings())

    process.crawl(CreditReportSpider, credit_account_id=account_id, username=username, password=password)
    process.start()
    _set_task_progress(100)


def capture(id):
    credit_report_account = CreditReportAccount.query.filter_by(id=id).first()
    password = current_app.cipher.decrypt(credit_report_account.password).decode()
    _crawl_credit_report(credit_report_account.id, credit_report_account.email, password)


if __name__ == '__main__':
    _crawl_credit_report(1, 'test1@consumerdirect.com', '12345678')
