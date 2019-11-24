# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Debt(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    creditor = scrapy.Field()
    type = scrapy.Field()
    ecoa = scrapy.Field()
    account_number = scrapy.Field()
    push = scrapy.Field()
    last_collector = scrapy.Field()
    collector_account_number = scrapy.Field()
    last_debt_status = scrapy.Field()
    days_delinquent = scrapy.Field()
    balance_original = scrapy.Field()
    payment_amount = scrapy.Field()
    credit_limit = scrapy.Field()
    graduation = scrapy.Field()
    last_update = scrapy.Field()
