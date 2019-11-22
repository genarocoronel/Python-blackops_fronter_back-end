from datetime import datetime, timedelta
import sqlite3

import pdfkit
import scrapy
from scrapy_splash import SplashRequest


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


class Crawler(scrapy.Spider):
    name = 'reports'

    username = 'test1@consumerdirect.com'
    password = '12345678'

    http_user = 'documentservicesolutions'
    http_pass = 'grapackerown'

    connection = sqlite3.connect('./reports.db')
    cursor = connection.cursor()

    start_urls = ['https://stage-sc.consumerdirect.com/login/']
    report_url = 'https://stage-sc.consumerdirect.com/member/credit-report/3b/'

    def parse(self, response):
        csrf = response.xpath("//input[@name='_csrf']/@value").get()

        return scrapy.FormRequest.from_response(
            response,
            formdata={'_csrf': csrf, 'loginType': 'CUSTOMER', 'j_username': self.username, 'j_password': self.password},
            callback=self.goto_report
        )

    def goto_report(self, response):
        yield SplashRequest(url=self.report_url, endpoint='execute', callback=self.parse_report, args={
                                    'html': 1,
                                    'wait': 10,
                                })

    def parse_report(self, response):
        self.cursor.execute("""CREATE TABLE reports (debt_name, creditor, account_type, ecoa, account_number, push,
                                last_collector, collector_account, last_debt_status, bureaus, days_delinquent, balance_original,
                                payment_amount, credit_limit, graduation, last_update)""")
        self.connection.commit()

        tables = response.xpath("""//div[@id='TokenDisplay']//td[@class='crWhiteTradelineHeader']/ancestor::table[2]""")
        self.log('Tables:')
        # self.log(tables)
        self.log(f'Length: {len(tables)}')
        # address = ''.join(response.xpath("""//div[@id='TokenDisplay']//table[6]//tr[@class='crTradelineHeader']//td[2]//span[@class='Rsmall']/text()""").extract())
        # address = address
        address = response.xpath(
            """//div[@id='TokenDisplay']//table[6]//tr[@class='crTradelineHeader']//td[2]//span[@class='Rsmall']/text()"""
            ).extract()[-1].replace('\r', ' ').replace('\t', '').replace('\n', '')
        if ',' in address:
            address = address.split(',')[1]
        limitation = get_limitations(address)
        for table in tables:
            row = dict()
            row['debt_name'] = row['creditor'] = table.xpath("./descendant::b/text()").get()
            row['account_number'] = self.get_cell(table,
                                                  "./descendant::b[contains(text(), 'Account #')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()",
                                                  [2, 3, 4])
            row['account_type'] = self.get_cell(table,
                                                "./descendant::b[contains(text(), 'Account Type')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()",
                                                [2, 3, 4])
            row['ecoa'] = self.get_cell(table,
                                        "./descendant::b[contains(text(), 'Account Description')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()",
                                        [2, 3, 4])
            row['push'] = False
            row['last_collector'] = None
            row['collector_account'] = None
            row['last_debt_status'] = None
            row['bureaus'] = None
            payment_status = self.get_cell(table,
                                           "./descendant::b[contains(text(), 'Payment Status')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()",
                                           [2, 3, 4])
            if payment_status == 'current':
                row['days_delinquent'] = 0
            elif payment_status == 'late 30 days':
                row['days_delinquent'] = 30
            else:
                row['days_delinquent'] = ''  # set for collection/chargeoff
            row['balance_original'] = normalize(self.get_cell(table,
                                                              "./descendant::b[contains(text(), 'Balance Owed')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()",
                                                              [2, 3, 4]))
            row['payment_amount'] = normalize(self.get_cell(table,
                                                            "./descendant::b[contains(text(), 'Payment Amount')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()",
                                                            [2, 3, 4]))
            row['credit_limit'] = normalize(self.get_cell(table,
                                                          "./descendant::b[contains(text(), 'Credit Limit')]/ancestor::tr[@class='crTableHeader']/td[{}]/text()",
                                                          [2, 3, 4]))
            last_payment = self.get_cell(table,
                                         "./descendant::b[contains(text(), 'Last Payment')]/ancestor::tr[@class='crLightTableBackground']/td[{}]/text()",
                                         [2, 3, 4])
            row['graduation'] = None
            if last_payment:
                if limitation:
                    row['graduation'] = datetime.strptime(last_payment, '%m/%d/%Y') + timedelta(days=360 * limitation)
            row['last_update'] = datetime.now()
            self.insert_row(row)
            self.log(row)
        pdfkit.from_string(response.text,
                           'report.pdf')

    def get_cell(self, table_el, row_xpath, params):
        for param in params:
            val = table_el.xpath(row_xpath.format(param)).get()
            if val:
                if '--' not in val:
                    return val.strip().lower()

    def insert_row(self, row):
        columns = ', '.join(row.keys())
        placeholders = ', '.join('?' * len(row))
        # self.log("INSERT INTO reports ({}) VALUES ({})".format(columns, placeholders))
        self.cursor.execute("INSERT INTO reports ({}) VALUES ({})".format(columns, placeholders), tuple(row.values()))
        self.connection.commit()
