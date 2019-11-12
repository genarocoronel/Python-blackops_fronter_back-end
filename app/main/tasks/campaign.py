import csv
import os
import uuid
from os import path

from flask import current_app as app
from filelock import FileLock

from app.main import db
from app.main.config import upload_location, prequal_id_counter_lock_file, prequal_id_counter_file
from app.main.model.campaign import Campaign


def _set_latest_prequal_id(value):
    lock = FileLock(prequal_id_counter_lock_file)
    with lock:
        open(prequal_id_counter_file, "w").write()


def _get_latest_prequal_id():
    lock = FileLock(prequal_id_counter_lock_file)
    with lock:
        if not path.isfile(prequal_id_counter_file):
            return None
        else:
            open(prequal_id_counter_file, "r").read()


def generate_mailer_file(campaign_id):
    app.logger.info('Executing generate_mailer_file...')
    campaign = Campaign.query.get(campaign_id)

    candidates = campaign.candidates.all()

    mapping = {'candidate.first_name': 'first', 'candidate.last_name': 'last', 'candidate.address': 'address',
               'candidate.city': 'city', 'candidate.state': 'st', 'candidate.zip5': 'zip',
               'campaign.phone': 'phone_numb', 'campaign.job_number': 'job_number',
               'campaign.mailing_date': 'mailing_da', 'campaign.offer_expire_date': 'offer_expi',
               'candidate.prequal_number': 'prequal', 'candidate.estimated_debt': 'debt', 'candidate.debt3': 'debt3',
               'candidate.debt15': 'debt15', 'candidate.debt2': 'debt2', 'candidate.debt215': 'debt215',
               'candidate.debt3_2': 'debt3_2', 'candidate.checkamt': 'checkamt', 'candidate.spellamt': 'spellamt',
               'candidate.debt315': 'debt315', 'candidate.year_interest': 'int_yr',
               'candidate.total_interest': 'tot_int', 'candidate.sav215': 'sav215', 'candidate.sav15': 'sav15',
               'candidate.sav315': 'sav315'}

    filters = {'debt': _money, 'debt3': _money, 'debt15': _money, 'debt2': _money, 'debt215': _money, 'debt3_2': _money,
               'checkamt': _money, 'debt315': _money, 'int_yr': _money, 'tot_int': _money, 'sav215': _money,
               'sav15': _money, 'sav315': _money}

    try:
        file_path = _get_mailer_file(campaign)

        lock = FileLock(prequal_id_counter_lock_file)
        with lock:
            if not path.isfile(prequal_id_counter_file):
                latest_prequal_id = 'A10000'
            else:
                latest_prequal_id = open(prequal_id_counter_file, "r").read()

            gen_prequal_func = _generate_prequal_id(latest_prequal_id)

            with open(file_path, 'w') as csvFile:
                writer = csv.DictWriter(csvFile, fieldnames=mapping.values(), quoting=csv.QUOTE_ALL)
                writer.writeheader()

                for candidate in candidates:
                    record = {}
                    if not candidate.prequal_number:
                        try:
                            latest_prequal_id = next(gen_prequal_func)
                        except StopIteration:
                            letter, number = latest_prequal_id[:1], latest_prequal_id[1:]
                            new_prequal_id = f'{chr(ord(letter) + 1)}10000'
                            gen_prequal_func = _generate_prequal_id(new_prequal_id)
                            latest_prequal_id = next(gen_prequal_func)

                        candidate.prequal_number = latest_prequal_id

                    for source, key in mapping.items():
                        model, attr = source.split('.')
                        if model == 'candidate':
                            record[key] = _filter(filters, key, getattr(candidate, attr, 'MISSING_VALUE'))
                        elif model == 'campaign':
                            record[key] = _filter(filters, key, getattr(campaign, attr, 'MISSING_VALUE'))
                        else:
                            record[key] = 'UNKNOWN_SOURCE_VALUE'

                    writer.writerow(record)

            campaign.mailer_file = file_path
            open(prequal_id_counter_file, 'w').write(latest_prequal_id)
            db.session.commit()
    finally:
        csvFile.close()


def _get_mailer_file(campaign):
    if campaign.mailer_file and path.isfile(campaign.mailer_file):
        file_path = campaign.mailer_file
    else:
        filename = f'{uuid.uuid4()}.csv'
        file_path = os.path.join(upload_location, filename)
    return file_path


def _filter(filter_mapping, key, value):
    if key in filter_mapping:
        return filter_mapping[key](value)
    else:
        return value


def _money(value):
    return "${:0,.0f}".format(value)


def _generate_prequal_id(latest_prequal_id, max_int=100000):
    letter, number = latest_prequal_id[:1], latest_prequal_id[1:]

    for i in range(int(number) + 1, max_int):
        yield f'{letter}{i}'
