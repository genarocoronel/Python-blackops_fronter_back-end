import re

import scrapy
from urllib.parse import urlparse

from scrapy_splash import SplashRequest

from ..items import Debt
from flask import current_app as app


class CreditReportSpider(scrapy.Spider):
    name = 'creditreport'

    # start_urls = ['file:///<your-local-html-file-path>']
    start_urls = ['https://stage-sc.consumerdirect.com/login/']

    http_user = 'documentservicesolutions'
    http_pass = 'grapackerown'

    credit_report_url = 'https://stage-sc.consumerdirect.com/member/credit-report/3b/'

    def __init__(self, credit_account_id=None, username=None, password=None, *args, **kwargs):
        super(CreditReportSpider, self).__init__(*args, **kwargs)
        app.logger.debug('Spidey initializing....')

        if not username or not password:
            raise Exception('username and password are required')
        self.credit_account_id = credit_account_id
        self.username = username
        self.password = password

    def parse(self, response):
        app.logger.debug('Spidey LIVE parsing....')
        #return self.simulated_parse()
        csrf = response.xpath("//input[@name='_csrf']/@value").get()
        
        if urlparse(response.url).scheme == 'file':
            return self.parse_credit_report(response)

        else:
            return scrapy.FormRequest.from_response(
                response,
                formdata={'_csrf': csrf, 'loginType': 'CUSTOMER', 'j_username': self.username, 'j_password': self.password},
                callback=self.visit_credit_report,
                dont_filter=True
            )

    def simulated_parse(self):
        app.logger.debug('Spidey Simulating parse....')
        state = 'FL'
        fake_debts = [
            {
                'type': 'Charge account',
                'debt_name': '1ST CAL MG',
                'acct_number_raw': '74635****',
                'ecoa': 'No description',
                'days_delinguent': 'Late 90 Days',
                'balance_original': '7,567',
                'payment_amount': '1,177',
                'credit_limit': '10000',
                'last_payment': ''
            },
            {
                'type': 'Charge account',
                'debt_name': 'HRSI BANK-WHIRL',
                'acct_number_raw': '1590577****',
                'ecoa': 'Individual',
                'days_delinguent': 'Late 30 Days',
                'balance_original': '276',
                'payment_amount': '20',
                'credit_limit': '1500',
                'last_payment': ''
            },
            {
                'type': 'Bank',
                'debt_name': 'HRSI BANK',
                'acct_number_raw': '101590577****',
                'ecoa': 'Individual',
                'days_delinguent': 'Current',
                'balance_original': '2165',
                'payment_amount': '200',
                'credit_limit': '',
                'last_payment': ''
            },
            {
                'type': 'Department/Variety and Other Retail',
                'debt_name': 'BURDINES',
                'acct_number_raw': '225563****',
                'ecoa': 'Individual',
                'days_delinguent': 'Current',
                'balance_original': '296',
                'payment_amount': '7',
                'credit_limit': '400',
                'last_payment': ''
            },
            {
                'type': 'Bank Credit Cards',
                'debt_name': 'CITIBANK NA',
                'acct_number_raw': '54241801****',
                'ecoa': 'Individual',
                'days_delinguent': 'Late 30 Days',
                'balance_original': '11,201',
                'payment_amount': '725',
                'credit_limit': '27500',
                'last_payment': ''
            },
        ]

        for debt_item in fake_debts:
            app.logger.debug(f'Spidey Processing debt: {debt_item["debt_name"]}')
            type = debt_item['type']
            if type is None:
                type = 'None Given'

            debt_name = debt_item['debt_name']
            acct_number_raw = debt_item['acct_number_raw']
            ecoa = debt_item['ecoa']
            days_delinguent = debt_item['days_delinguent']
            balance_original = debt_item['balance_original']
            payment_amount = debt_item['payment_amount']
            credit_limit = debt_item['credit_limit']
            last_payment = debt_item['last_payment']

            yield Debt(
                credit_account_id=self.credit_account_id,
                name=debt_name,
                creditor=debt_name,
                type=type,
                ecoa=ecoa,
                account_number=acct_number_raw,
                days_delinquent=days_delinguent,
                balance_original=balance_original,
                payment_amount=payment_amount,
                credit_limit=credit_limit,
                last_payment=last_payment,
                state=state,
            )
    
    def visit_credit_report(self, response):
        app.logger.debug('Spidey SIMPLE visiting credit report page...')
        yield scrapy.Request(url=self.credit_report_url, callback=self.check_for_order_prompt, dont_filter=True)

    def visit_credit_report_splash(self, response):
        app.logger.debug('Spidey SPLASH visiting credit report page...')
        yield SplashRequest(url=self.credit_report_url, callback=self.parse_credit_report, args={'wait': 10})

    def check_for_order_prompt(self, response):
        you_are_ordering_text = response.xpath("//div[@id='confirm']/div[@class='content-heading']/h3/text()").get()
        if you_are_ordering_text and 'you are ordering' == you_are_ordering_text.lower():
            app.logger.debug('Spidey encountered ORDER PROMPT. Submitting form...')
            return scrapy.FormRequest.from_response(
                response,
                formdata={'isConfirmedTerms': 'on'},
                callback=self.visit_credit_report_splash
            )
            # raise Exception('Still need to order 3B report before scrape')
            # POST form to 'https://stage-sc.consumerdirect.com/member/credit-report/3b/confirm.htm'
            # with data: 'isConfirmedTerms: on'
        else:
            app.logger.debug('Spidey did not encounter ORDER PROMPT. Moving on...')
            return self.visit_credit_report_splash(response)

    def parse_credit_report(self, response):
        app.logger.debug('Spidey parsing report now...')
        address = ' '.join(response.xpath("//div[@id='TokenDisplay']//table[6]//tr[@class='crTradelineHeader']//td[2]//span[@class='Rsmall']/span/text()").getall()).replace('\t', '').replace('\n', '')
        state_match = re.search(r'.*,\W+(\w{2})\W+[0-9]+', address, re.M | re.I)
        state = state_match.group(1) if state_match else None

        app.logger.debug(f'Spidey printing response..')
        print(response)

        # This is where the spider is dying: The if statement finds the "debt_tables" NULL, and throws 
        debt_tables = response.xpath("//div[@id='TokenDisplay']//td[@class='crWhiteTradelineHeader']/ancestor::table[2]")
        if debt_tables:
            for debt_table in debt_tables:
                type = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account Type')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                if type is None:
                    type = 'None Given'
                debt_name = debt_table.xpath("./descendant::td[@class='crWhiteTradelineHeader'][2]/b/text()").get()
                acct_number_raw = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account #')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()", [2, 3, 4])
                
                account_number = ''
                if acct_number_raw:
                    account_number = re.findall(r"[0-9]+\*+", acct_number_raw.rstrip())[0]

                ecoa = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Account Description')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                days_delinguent = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Payment Status')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                balance_original = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Balance Owed')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()", [2, 3, 4])
                payment_amount = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Payment Amount')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                credit_limit = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Credit Limit')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()", [2, 3, 4])
                last_payment = self._traverse_columns_for_value(debt_table, "./descendant::b[contains(text(), 'Last Payment')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()", [2, 3, 4])

                app.logger.debug(f'Spidey processing Debt with Name: {debt_name}')
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
            app.logger.debug('Spidey did NOT find any DEBT TABLES!')
            raise Exception(f'Failed to capture debts for credit report account with ID: {self.credit_account_id}')

    def _traverse_columns_for_value(self, table_el, row_xpath, params):
        # TODO: possibly have 'params' be a dict  that would allow for formatting key-value pairs into a formatted string
        for param in params:
            val = table_el.xpath(row_xpath.format(param)).get()
            if val and '--' not in val:
                return val.strip()
