import werkzeug
from flask_restplus import reqparse

file_upload = reqparse.RequestParser()
file_upload.add_argument('csv_file',
                         type=werkzeug.datastructures.FileStorage,
                         location='files',
                         required=True,
                         help='CSV file')
