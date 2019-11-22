# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import sqlite3


class ReportCrawlerPipeline(object):
    def __init__(self):
        # self.connection = sqlite3.connect('./scrapedata.db')
        # self.cursor = self.connection.cursor()

        # self.cursor.execute("""CREATE TABLE reports (debt_name, creditor, type, ecoa, account_number, push,
        #         last_collector, collector_account, last_debt_status, bureaus, days_delinquent, balance_original, payment_amount,
        #         credit_limit, graduation)""")
        # self.connection.commit()
        pass

    def process_item(self, item, spider):
        # columns = ', '.join(item.keys())
        # placeholders = ', '.join('?' * len(item))
        # self.cursor.execute("INSERT INTO reports ({}) VALUES ({})".format(columns, placeholders), item.values())
        # self.connection.commit()
        return item
