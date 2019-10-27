import os

from flask_restplus import Resource
from werkzeug.utils import secure_filename

from app.main.config import upload_location
from app.main.service.candidate_service import save_new_candidate_import, save_changes
from ..util.dto import CandidateDto

api = CandidateDto.api
_candidate_upload = CandidateDto.candidate_upload


@api.route('/upload')
class CandidateUpload(Resource):
    @api.doc('create candidates from file')
    @api.expect(_candidate_upload, validate=True)
    def post(self):
        """ Creates Candidates from file """

        args = _candidate_upload.parse_args()
        file = args['csv_file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_location, filename)
            file.save(file_path)

            candidate_import = save_new_candidate_import(dict(file_path=file_path))
            task = candidate_import.launch_task('parse_candidate_file',
                                                'Parse uploaded candidate file and load db with entries')

            save_changes()

            resp = {'task_id': task.id}
            return resp, 200

        else:
            return {'status': 'failed', 'message': 'No file was provided'}, 409