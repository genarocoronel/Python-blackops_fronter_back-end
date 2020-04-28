import os

from werkzeug.utils import secure_filename
from flask import send_from_directory


def save_file(file, file_name, path):
    if not os.path.isdir(path):
        raise Exception('You did not provide a directory path')

    filename = generate_secure_filename(file_name)
    filepath = os.path.join(path, filename)
    file.save(filepath)
    return filename, filepath


def open_file(file_path, mode):
    return open(file_path, mode)


def stream_file(path, file_name, as_attachment=False, mimetype=None):
    if not os.path.isdir(path):
        raise Exception('You did not provide a directory path')

    return send_from_directory(path, filename=file_name, as_attachment=as_attachment, mimetype=mimetype)


def delete_file(file_path):
    if not os.path.isfile(file_path):
        raise Exception('You did not specify a path to a file')

    os.remove(file_path)


def generate_secure_filename(untrusted_file_name):
    return secure_filename(untrusted_file_name)


def get_extension_for_filename(file_name):
    filename_part, fileext_part = os.path.splitext(file_name)
    return fileext_part


def get_mime_from_extension(extension):
    mime = None
    if extension in ('.jpg', '.jpeg'):
        mime = 'image/jpeg'
    elif extension == '.png':
        mime = 'image/png'
    elif extension == '.gif':
        mime = 'image/gif'
    elif extension == '.pdf':
        mime = 'application/pdf'

    return mime
