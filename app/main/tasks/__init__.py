import csv

from rq import get_current_job

from app.main import db
from app.main.model.candidate import CandidateImport, CandidateImportStatus
from app.main.model.client import ClientType
from app.main.model.task import ImportTask
from app.main.service.client_service import save_new_client
from flask import current_app as app


def _set_task_progress(import_request, progress, success=True, message=None):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
    job.save_meta()
    task = ImportTask.query.get(job.get_id())

    if progress >= 100:
        task.complete = True
        import_request.status = CandidateImportStatus.FINISHED if success else CandidateImportStatus.ERROR
    else:
        import_request.status = CandidateImportStatus.RUNNING
    db.session.commit()


def parse_candidate_file(import_id):
    app.logger.debug('Executing parse_candidate_file...')
    import_request = CandidateImport.query.get(import_id)  # type: CandidateImport
    _set_task_progress(import_request, 0)

    app.logger.info(f'Importing {import_request.file}...')
    with open(import_request.file, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        row_count = sum(1 for line in csvfile) - 1
        csvfile.seek(0)
        app.logger.info(f'{row_count} records identified for import')

        fields = csvreader.__next__()
        app.logger.debug(f'Column names are {", ".join(fields)}')
        keys = [key.upper() for key in fields]

        line_num = 0
        for row in csvreader:
            data = {
                'suffix': row[keys.index('SUFFIX')],
                'first_name': row[keys.index('FNAME')],
                'last_name': row[keys.index('LNAME')],
                'middle_initial': row[keys.index('MI')],
                'email': None,
                'language': 'en',
                'phone': None,
                'address': row[keys.index('ADDRESS')],
                'city': row[keys.index('CITY')],
                'state': row[keys.index('STATE')],
                'zip': convert_to_int(row[keys.index('ZIP')]),
                'zip4': convert_to_int(row[keys.index('ZIP4')]),
                'county': row[keys.index('COUNTY')],
                'crrt': row[keys.index('CRRT')],
                'dpbc': convert_to_int(row[keys.index('DPBC')]),
                'fips': convert_to_int(row[keys.index('FIPS')]),
                'estimated_debt': convert_to_int(row[keys.index('EST DEBT')].replace(',', ''))
            }
            result, _ = save_new_client(data, ClientType.candidate)
            if 'success' == result['status']:
                # app.logger.debug('{first_name} {last_name} was saved successfully'.format(**data))
                pass
            # else:
                # app.logger.info('{first_name} {last_name} failed to save'.format(**data))
                # app.logger.info(result['message'])

            line_num += 1
            _set_task_progress(import_request, (line_num / row_count) * 100)

    _set_task_progress(import_request, 100)


def convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        return 0
