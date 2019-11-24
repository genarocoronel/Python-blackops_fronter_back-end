import re

import scrapy
from scrapy import Request
from urllib.parse import urlparse

from scrapy.shell import inspect_response
from scrapy.utils.response import open_in_browser
from scrapy_splash import SplashRequest

from ..items import Debt


class CreditReportSpider(scrapy.Spider):
    name = 'creditreport'

    # start_urls = ['file:///<your-local-html-file-path>']
    start_urls = ['https://stage-sc.consumerdirect.com/login/']

    http_user = 'documentservicesolutions'
    http_pass = 'grapackerown'

    credit_report_url = 'https://stage-sc.consumerdirect.com/member/credit-report/3b/'

    def parse(self, response):
        csrf = response.xpath("//input[@name='_csrf']/@value").get()
        username = 'test1@consumerdirect.com'
        password = '12345678'

        if urlparse(response.url).scheme == 'file':
            return self.parse_credit_report(response)
        else:
            return scrapy.FormRequest.from_response(
                response,
                formdata={'_csrf': csrf, 'loginType': 'CUSTOMER', 'j_username': username, 'j_password': password},
                callback=self.visit_credit_report
            )

    def visit_credit_report(self, response):
        yield SplashRequest(url=self.credit_report_url, callback=self.parse_credit_report, args={'wait': 10})

    def parse_credit_report(self, response):
        debt_tables = response.xpath("//div[@id='TokenDisplay']//td[@class='crWhiteTradelineHeader']/ancestor::table[2]")
        if debt_tables:
            for debt_table in debt_tables:
                type = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account Type')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                debt_name = debt_table.xpath("./descendant::td[@class='crWhiteTradelineHeader'][2]/b/text()").get()
                acct_number_raw = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account #')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()", [2, 3, 4])
                account_number = re.findall(r"[0-9]+\*+", acct_number_raw.rstrip())[0]
                ecoa = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account Description')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                days_delinguent = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Payment Status')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])

                yield Debt(
                    name=debt_name,
                    creditor=debt_name,
                    type=type,
                    ecoa=ecoa,
                    account_number=account_number,
                    push=False,
                    days_delinquent=days_delinguent
                )
        else:
            inspect_response(response, self)

    def _traverse_columns_for_value(self, table_el, row_xpath, params):
        # TODO: possibly have 'params' be a dict  that would allow for formating key-value pairs into a formatted string
        for param in params:
            val = table_el.xpath(row_xpath.format(param)).get()
            if '--' not in val:
                return val
