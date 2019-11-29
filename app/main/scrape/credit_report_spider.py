import os
import re
import uuid
import sqlite3
import pdfkit
import scrapy
from datetime import datetime, timedelta
from scrapy.crawler import CrawlerProcess
from scrapy_splash import SplashRequest
from flask import current_app
from w3lib.http import basic_auth_header
from lxml.html import fromstring
import html
from app.main import db
from app.main.model.credit_report_account import CreditReportData
from app.main.model.task import ScrapeTask


DAYS_DELINQUENT_PATTERN = re.compile(r' (\d+)')
REPORT_PATH = 'report.pdf'
CSS_FOLDER = 'report_css'


def normalize(string: str):
    if string:
        if '.' in string:
            return float(string.replace('$', '').replace(',', ''))
        return int(string.replace('$', '').replace(',', ''))


def get_limitations(address: str) -> int:
    state = ''.join(letter for letter in address if letter.isalpha()).strip()
    if len(state) == 2:
        limitation_dict = {
            'AL': 6, 'AK': 3, 'AZ': 6, 'AR': 5, 'CA': 4, 'CO': 6, 'CT': 6, 'DE': 3, 'FL': 5, 'GA': 6, 'HI': 6, 'ID': 5,
            'IL': 10, 'IN': 6, 'IA': 10, 'KS': 5, 'KY': 10, 'LA': 10, 'ME': 6, 'MD': 3, 'MA': 6, 'MI': 6, 'MN': 6,
            'MS': 3, 'MO': 10, 'MT': 8, 'NE': 5, 'NV': 6, 'NH': 3, 'NJ': 6, 'NM': 6, 'NY': 6, 'NC': 3, 'ND': 6, 'OH': 8,
            'OK': 5, 'OR': 6, 'PA': 4, 'RI': 10, 'SC': 3, 'SD': 6, 'TN': 6, 'TX': 4, 'UT': 6, 'VT': 6, 'VA': 5, 'WA': 6,
            'WV': 10, 'WI': 6, 'WY': 10
        }
        return limitation_dict.get(state.upper())


class CreditReportSpider(scrapy.Spider):
    name = 'credit_report_spider'
    allowed_domains = ["consumerdirect.com", "cc2-live.sd.demo.truelink.com"]

    def __init__(self, *args):
        self.account_id, self.username, self.password = args
        self.report_url = 'https://stage-sc.consumerdirect.com/member/credit-report/3b/'
        self.login_url = 'https://stage-sc.consumerdirect.com/login/'
        self.auth = basic_auth_header(
            current_app.config['SMART_CREDIT_HTTP_USER'],
            current_app.config['SMART_CREDIT_HTTP_PASS']
        )
        self.set_css()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/webp,image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8,ru;q=0.7',
            'Authorization': self.auth,
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'stage-sc.consumerdirect.com',
            'Origin': 'https://stage-sc.consumerdirect.com',
            'Referer': 'https://stage-sc.consumerdirect.com/login/',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/78.0.3904.97 Safari/537.36'
        }

    def set_css(self,):
        basedir = os.path.abspath(os.path.dirname(__file__))
        css_path = os.path.join(basedir, CSS_FOLDER)
        self.css = [
            os.path.join(css_path, f) for f in os.listdir(css_path)
            if os.path.isfile(os.path.join(css_path, f))
            and f.endswith('.css')
        ]

    def start_requests(self):
        yield scrapy.Request(
            self.login_url,
            callback=self.proceed_for_login,
            headers={'Authorization': self.auth},
        )

    def proceed_for_login(self, response):
        csrf = response.xpath("//input[@name='_csrf']/@value").get()
        formdata = {
            '_csrf': csrf,
            'loginType': 'CUSTOMER',
            'j_username': self.username,
            'j_password': self.password,
            'rememberMe': 'on',
        }
        yield scrapy.FormRequest(
            self.login_url.strip('/'),
            formdata=formdata,
            callback=self.after_login,
            headers=self.headers
        )

    def after_login(self, response):
        yield scrapy.Request(
            self.report_url,
            callback=self.get_report_html,
            headers=self.headers
            )

    def get_report_html(self, response):
        url = response.xpath(
            '//div[@class="container content"]/'
            'following-sibling::script[1]/@src').get()
        yield scrapy.Request(url, callback=self.parse_report_data)

    def parse_report_data(self, response):
        pattern = re.compile(r'\.html\(\"(.*?)\"\);')
        match = pattern.findall(response.text)
        converted_data = match[0].replace('\\u003c', '<')\
                                 .replace('\\u003e', '>')\
                                 .replace('\\r', '\r')\
                                 .replace('\\n', '\n')\
                                 .replace('\\t', '\t')\
                                 .replace('\\"', '"')

        response = fromstring(converted_data)
        address = response.xpath(
            "//tr[@class='crTradelineHeader']//td[2]/descendant::text()"
            )[1].replace('\r', ' ').replace('\t', '').replace('\n', '')
        if ',' in address:
            address = address.split(',')[-1].split()[0].strip()
        limitation = get_limitations(address)
        tables = response.xpath(
            '//table[@border="1" and '
            './/table[@class="crLightTableBackground"]]')
        scraped_data = list()
        for table in tables:
            debt_name = creditor = table.xpath(
                './/td[@class="crWhiteTradelineHeader"]/b/text()')[0]
            account_type = [value for value in table.xpath(
                './/td[descendant::text()="Account Type:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            account_type = account_type[0] if account_type else None

            ecoa = [value for value in table.xpath(
                './/td[descendant::text()="Account Description:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            ecoa = ecoa[0].strip() if ecoa else None

            account_number = [value for value in table.xpath(
                './/td[descendant::text()="Account #:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            account_number = account_number[0].strip()\
                if account_number else None

            payment_status = [value for value in table.xpath(
                './/td[descendant::text()="Payment Status:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            payment_status = payment_status[0].strip()\
                if payment_status else None
            days_delinquent = 0
            if payment_status:
                match = DAYS_DELINQUENT_PATTERN.findall(payment_status)
                if match:
                    days_delinquent = match[0]

            balance_original = [value for value in table.xpath(
                './/td[descendant::text()="Balance Owed:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            balance_original = normalize(balance_original[0].strip())\
                if balance_original else None

            payment_amount = [value for value in table.xpath(
                './/td[descendant::text()="Payment Amount:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            payment_amount = normalize(payment_amount[0].strip())\
                if payment_amount else None

            credit_limit = [value for value in table.xpath(
                './/td[descendant::text()="Credit Limit:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            credit_limit = normalize(credit_limit[0].strip())\
                if credit_limit else None

            last_payment = [value for value in table.xpath(
                './/td[descendant::text()="Last Payment:"]'
                '/following-sibling::td/text()')
                if '--' not in value]
            last_payment = last_payment[0].strip() if last_payment else None
            graduation = None
            if last_payment and limitation:
                graduation = datetime.strptime(last_payment, '%m/%d/%Y') +\
                    timedelta(days=360 * limitation)

            last_update = datetime.utcnow()

            report_data = CreditReportData(
                account_id=self.account_id,
                public_id=str(uuid.uuid4()),
                debt_name=debt_name,
                creditor=creditor,
                ecoa=ecoa,
                account_number=account_number,
                account_type=account_type,
                days_delinquent=days_delinquent,
                balance_original=balance_original,
                payment_amount=payment_amount,
                credit_limit=credit_limit,
                graduation=graduation,
                last_update=last_update
                )
            scraped_data.append(report_data)

        self.remove_old_data()
        self.update_new_data(scraped_data)
        self.mark_complete()

        # ------ FOR PDF Converson -----------
        basedir = os.path.abspath(os.path.dirname(__file__))
        report_path = os.path.join(basedir, REPORT_PATH)
        pdfkit.from_string(
            converted_data.replace('\xa0', '').replace('®', ''),
            report_path,
            css=self.css
        )

    def remove_old_data(self,):
        existing_data = CreditReportData.query.filter_by(
            account_id=self.account_id).all()
        for d in existing_data:
            db.session.delete(d)
        db.session.commit()

    def update_new_data(self, scraped_data):
        for d in scraped_data:
            db.session.add(d)
        db.session.commit()

    def mark_complete(self,):
        task = ScrapeTask.query.filter_by(
            account_id=self.account_id, complete=False).first()
        if task:
            setattr(task, 'complete', True)
            setattr(task, 'updated_on', datetime.utcnow())
            db.session.add(task)
            db.session.commit()


def run(*args):
    settings = {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 5,
        'RETRY_HTTP_CODES': [403, 405, 429, 500, 503],
        'RETRY_TIMES': 2,
    }
    process = CrawlerProcess(settings)
    process.crawl(CreditReportSpider, *args)
    process.start()


if __name__ == '__main__':
    run('test1@consumerdirect.com', '12345678')
