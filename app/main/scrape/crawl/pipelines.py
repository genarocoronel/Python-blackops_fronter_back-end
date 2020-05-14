# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import datetime
import re
import uuid

from app.main import db
from app.main.model.credit_report_account import CreditReportData


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


def _sanitize_days_delinquent(value):
    result = re.search(r'[0-9]+', value)
    if result:
        return int(result.group())
    return 0


def _sanitize_dollar_amount(value):
    if value:
        return int(value.replace('$', '').replace(',', ''))
    return None


class CreditReportPipeline(object):
    def __init__(self):
        self._cached_debt_names = {}

    def process_item(self, item, spider):
        state = item.get('state')
        if state:
            limitation = get_limitations(state)
        else:
            limitation = None

        raw_last_payment = item.get('last_payment')
        if raw_last_payment and limitation:
            graduation = datetime.datetime.strptime(raw_last_payment, '%m/%d/%Y') + datetime.timedelta(days=365 * limitation)
        else:
            graduation = None

        credit_account_id = item.get('credit_account_id')
        debt_name = item.get('name') if item.get('name') else 'NO NAME'

        # TODO: I know there is some way to user `any`, `filter` and/or a `lambda` to clean this up
        exists = False
        for key, value in self._cached_debt_names.items():
            if re.match(f'^{debt_name}$', key):
                exists = True
                new_count = self._cached_debt_names[debt_name] + 1
                self._cached_debt_names[debt_name] = new_count
                debt_name = f'{debt_name}{new_count}'
                break

        if not exists:
            self._cached_debt_names[debt_name] = 1

        existing_debt_entry = CreditReportData.query.filter_by(account_id=credit_account_id, debt_name=debt_name).first()
        if existing_debt_entry:
            existing_debt_entry.ecoa = item.get('ecoa')
            existing_debt_entry.account_number = item.get('account_number')
            existing_debt_entry.account_type = item.get('type')
            existing_debt_entry.days_delinquent = _sanitize_days_delinquent(item.get('days_delinquent'))
            existing_debt_entry.balance_original = _sanitize_dollar_amount(item.get('balance_original'))
            existing_debt_entry.payment_amount = _sanitize_dollar_amount(item.get('payment_amount'))
            existing_debt_entry.credit_limit = _sanitize_dollar_amount(item.get('credit_limit'))
            existing_debt_entry.graduation = graduation
            existing_debt_entry.last_update = datetime.datetime.utcnow()

            db.session.add(existing_debt_entry)
            return existing_debt_entry.__dict__
        else:
            new_credit_report_debt = CreditReportData(
                public_id=str(uuid.uuid4()),
                account_id=credit_account_id,
                debt_name=debt_name,
                creditor=debt_name,
                ecoa=item.get('ecoa'),
                account_number=item.get('account_number'),
                account_type=item.get('type'),
                days_delinquent=_sanitize_days_delinquent(item.get('days_delinquent')),
                balance_original=_sanitize_dollar_amount(item.get('balance_original')),
                payment_amount=_sanitize_dollar_amount(item.get('payment_amount')),
                credit_limit=_sanitize_dollar_amount(item.get('credit_limit')),
                graduation=graduation,
                last_update=datetime.datetime.utcnow(),
                push=False,
                last_debt_status=None,
                bureaus=None,
            )

            db.session.add(new_credit_report_debt)
            return new_credit_report_debt.__dict__

    def close_spider(self, spider):
        db.session.commit()
