import re

import scrapy
from urllib.parse import urlparse

from scrapy.shell import inspect_response
from scrapy_splash import SplashRequest

from ..items import Debt


class CreditReportSpider(scrapy.Spider):
    name = 'creditreport'

    # start_urls = ['file:///<your-local-html-file-path>']
    start_urls = ['https://stage-sc.consumerdirect.com/login/']

    http_user = 'documentservicesolutions'
    http_pass = 'grapackerown'

    credit_report_url = 'https://stage-sc.consumerdirect.com/member/credit-report/3b/'

    def __init__(self, credit_account_id=None, username=None, password=None, *args, **kwargs):
        super(CreditReportSpider, self).__init__(*args, **kwargs)

        if not username or not password:
            raise Exception('username and password are required')
        self.credit_account_id = credit_account_id
        self.username = username
        self.password = password

    def parse(self, response):
        csrf = response.xpath("//input[@name='_csrf']/@value").get()

        if urlparse(response.url).scheme == 'file':
            return self.parse_credit_report(response)
        else:
            return scrapy.FormRequest.from_response(
                response,
                formdata={'_csrf': csrf, 'loginType': 'CUSTOMER', 'j_username': self.username, 'j_password': self.password},
                callback=self.visit_credit_report
            )

    def visit_credit_report(self, response):
        yield SplashRequest(url=self.credit_report_url, callback=self.parse_credit_report, args={'wait': 10})

    def parse_credit_report(self, response):
        address = ' '.join(response.xpath("//div[@id='TokenDisplay']//table[6]//tr[@class='crTradelineHeader']//td[2]//span[@class='Rsmall']/span/text()").getall()).replace('\t', '').replace('\n', '')
        state_match = re.search(r'.*,\W+(\w{2})\W+[0-9]+', address, re.M | re.I)
        state = state_match.group(1) if state_match else None
        # state = state_match.group(1)

        debt_tables = response.xpath("//div[@id='TokenDisplay']//td[@class='crWhiteTradelineHeader']/ancestor::table[2]")
        if debt_tables:
            for debt_table in debt_tables:
                type = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account Type')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                debt_name = debt_table.xpath("./descendant::td[@class='crWhiteTradelineHeader'][2]/b/text()").get()
                acct_number_raw = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account #')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()", [2, 3, 4])
                account_number = re.findall(r"[0-9]+\*+", acct_number_raw.rstrip())[0]
                ecoa = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account Description')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                days_delinguent = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Payment Status')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                balance_original = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Balance Owed')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()", [2, 3, 4])
                payment_amount = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Payment Amount')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                credit_limit = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Credit Limit')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                last_payment = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Last Payment')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()", [2, 3, 4])

                yield Debt(
                    credit_account_id=self.credit_account_id,
                    name=debt_name,
                    creditor=debt_name,
                    type=type,
                    ecoa=ecoa,
                    account_number=account_number,
                    days_delinquent=days_delinguent,
                    balance_original=balance_original,
                    payment_amount=payment_amount,
                    credit_limit=credit_limit,
                    last_payment=last_payment,
                    state=state,
                )
        else:
            inspect_response(response, self)

    def _traverse_columns_for_value(self, table_el, row_xpath, params):
        # TODO: possibly have 'params' be a dict  that would allow for formatting key-value pairs into a formatted string
        for param in params:
            val = table_el.xpath(row_xpath.format(param)).get()
            if '--' not in val:
                return val.strip()
