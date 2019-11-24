import csv

from rq import get_current_job
import inflect

from app.main import db
from app.main.model.candidate import CandidateImport, CandidateImportStatus
from app.main.model.task import ImportTask
from app.main.service.candidate_service import save_new_candidate
from flask import current_app as app


def _set_task_progress(import_request, progress, success=True, message=''):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
    job.save_meta()
    task = ImportTask.query.get(job.get_id())

    if progress >= 100:
        task.complete = True
        job.meta['message'] = message
        import_request.status = CandidateImportStatus.FINISHED if success else CandidateImportStatus.ERROR

    elif not success:
        task.complete = True
        task.message = message
        import_request.status = CandidateImportStatus.ERROR

    else:
        import_request.status = CandidateImportStatus.RUNNING
    db.session.commit()


def parse_candidate_file(import_id):
    app.logger.debug('Executing parse_candidate_file...')
    import_request = CandidateImport.query.get(import_id)  # type: CandidateImport
    _set_task_progress(import_request, 0)

    app.logger.info(f'Importing {import_request.file}...')
    with open(import_request.file, 'r') as csvfile:
        p = inflect.engine()
        csvreader = csv.reader(csvfile, delimiter=',')
        row_count = sum(1 for line in csvfile) - 1
        csvfile.seek(0)
        app.logger.info(f'{row_count} records identified for import')

        fields = csvreader.__next__()
        app.logger.debug(f'Column names are {", ".join(fields)}')
        keys = [key.upper() for key in fields]

        line_num = 0
        for row in csvreader:
            try:
                estimated_debt_str = row[keys.index('EST RVLV')].replace(',', '')
                estimated_debt = convert_to_int(estimated_debt_str)
                debt3 = round(0.03 * estimated_debt)
                debt15 = round((estimated_debt + (estimated_debt * 0.06)) / 60)
                debt2 = estimated_debt - 5000
                debt215 = round((debt2 + (debt2 * 0.06)) / 60)
                debt3_2 = estimated_debt + 5000
                checkamt = estimated_debt + 5000
                spellamt = '{} {}'.format(p.number_to_words(checkamt).title(), 'Dollars and No Cents')
                debt315 = round((debt3_2 + (debt3_2 * 0.06)) / 60)
                year_interest = round(estimated_debt * 0.1899)
                total_interest = year_interest * 22
                sav215 = round((((debt2 * 0.03) - debt215) * 12) - 4)
                sav15 = (debt3 * 12) - (debt15 * 12)
                sav315 = (((debt3_2 * 0.03) - debt315) * 12) + 4

                data = {
                    'suffix': row[keys.index('SUFFIX')],
                    'first_name': row[keys.index('FNAME')],
                    'last_name': row[keys.index('LNAME')],
                    'middle_initial': row[keys.index('MI')],
                    'email': None,
                    'language': 'unknown',
                    'phone': None,
                    'address': row[keys.index('ADDRESS')],
                    'city': row[keys.index('CITY')],
                    'state': row[keys.index('STATE')],
                    'zip': row[keys.index('ZIP')],
                    'zip4': row[keys.index('ZIP4')],
                    'estimated_debt': estimated_debt,
                    'debt3': debt3,
                    'debt15': debt15,
                    'debt2': debt2,
                    'debt215': debt215,
                    'debt3_2': debt3_2,
                    'checkamt': checkamt,
                    'spellamt': spellamt,
                    'debt315': debt315,
                    'year_interest': year_interest,
                    'total_interest': total_interest,
                    'sav215': sav215,
                    'sav15': sav15,
                    'sav315': sav315,
                    'import_record': import_request
                }
                result, _ = save_new_candidate(data)
                if 'success' == result['status']:
                    # app.logger.debug('{first_name} {last_name} was saved successfully'.format(**data))
                    pass
                # else:
                # app.logger.info('{first_name} {last_name} failed to save'.format(**data))
                # app.logger.info(result['message'])

                line_num += 1
                _set_task_progress(import_request, (line_num / row_count) * 100)
            except ValueError as ve:
                _set_task_progress(import_request, (line_num / row_count) * 100, False, str(ve))
                return
            except Exception as e:
                _set_task_progress(import_request, (line_num / row_count) * 100, False, str(e))
                return

    _set_task_progress(import_request, 100)


def convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        return 0
