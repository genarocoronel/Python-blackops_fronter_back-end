import os
import uuid
import time
import datetime

from werkzeug.utils import secure_filename
from flask import g, send_from_directory
from flask import current_app as app

from app.main.core.errors import BadRequestError, NotFoundError
from app.main.core.rac import RACRoles
from app.main.config import upload_location
from app.main import db
from app.main.model.docproc import (DocprocChannel, DocprocType, DocprocStatus, 
    DocprocNote, Docproc)
from app.main.service.user_service import get_user_by_id, get_request_user
from app.main.service.client_service import get_client_by_id

ALLOWED_DOC_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])

def get_all_docs():
    """ Gets all Doc to Process """
    docs = []
    curr_user = get_request_user()
    if curr_user.role.name == RACRoles.DOC_PROCESS_REP.value:
        doc_records = Docproc.query.filter_by(docproc_user_id=curr_user.id).all()
    else:
        doc_records = Docproc.query.filter_by().all()
        
    if doc_records:
        for doc_item in doc_records:
            tmp_doc = synth_doc(doc_item)
            docs.append(tmp_doc)
    
    return docs


def get_doc_by_pubid(public_id):
    """ Gets a Doc by Public ID """
    return Docproc.query.filter_by(public_id=public_id).first()


def get_docproc_types():
    """ Gets all known Doc Process Types """
    return DocprocType.query.filter_by().all()


def get_doctype_by_pubid(public_id):
    """ Gets a Doc Type Public ID """
    return DocprocType.query.filter_by(public_id=public_id).first()


def assign_for_processing(doc, docproc_user):
    """ Assigns a Doc to a User for processing """
    if docproc_user.role.name != RACRoles.DOC_PROCESS_REP.value:
        raise BadRequestError(f'Assignee user must be a member of the Doc Process Role')

    doc.docproc_user_id = docproc_user.id
    db.session.add(doc)
    _save_changes()

    return synth_doc(doc)


def move_to_client_dossier(doc, client):
    """ Moves a Doc to a Client dossier """
    doc.client_id = client.id
    db.session.add(doc)
    _save_changes()

    return synth_doc(doc)


def update_doc(doc, data):
    """ Updates a Doc """
    for attr in data:
        if hasattr(doc, attr):
            if attr == 'type':
                requested_type = get_doctype_by_pubid(data.get(attr)['public_id'])
                if not requested_type:
                    raise NotFoundError(f"The requested type with ID {attr['public_id']} could not be found.")
                doc.type = requested_type
            
            else:
                setattr(doc, attr, data.get(attr))

    _save_changes(doc)

    return synth_doc(doc)


def allowed_doc_file_kinds(filename):
    """ Gets whether a given filename is of allowed extension for Doc Processing """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS


def attach_file_to_doc(doc, file):
    """ Saves and attaches a File to a Doc """
    orig_filename = secure_filename(file.filename)
    filename_part, fileext_part = os.path.splitext(orig_filename)
    ms = time.time()
    safe_filename = 'docproc_{}_{}{}'.format(doc.public_id, ms, fileext_part)
    #TODO - Refactor for storing to AWS S3 bucket
    file_path = os.path.join(upload_location, safe_filename)
    file.save(file_path)

    return update_doc(doc, dict(file_name=safe_filename, orig_file_name=orig_filename))


def stream_doc_file(doc):
    extension = get_file_extension(doc.file_name)    
    mime = get_mime_from_extension(extension)

    # TODO - Refactor for streaming from AWS S3 bucket
    return send_from_directory(upload_location, filename=doc.file_name, as_attachment=False, mimetype=mime)
    

def get_mime_from_extension(extension):
    mime = None
    if extension in ('.jpg', '.jpeg'):
        mime = 'image/jpeg'
    elif extension == '.png':
        mime = 'image/png'
    elif extension == '.gif':
        mime == 'image/gif'
    elif extension == '.pdf':
        mime == 'application/pdf'

    return mime


def get_doc_file_uri(doc):
    return os.path.join(upload_location, doc.file_name)


def get_file_extension(filename):
    _, fileext_part = os.path.splitext(filename)
    return fileext_part


def create_doc_manual(data):
    """ Creates a new Doc manually """
    curr_user = get_request_user()

    doc = Docproc(
        public_id = str(uuid.uuid4()),
        doc_name=data['doc_name'],
        source_channel=DocprocChannel.MAIL.value,
        status=DocprocStatus.NEW.value,
        inserted_on=datetime.datetime.utcnow(),
        created_by_username = curr_user.username,
        updated_on=datetime.datetime.utcnow(),
        updated_by_username=curr_user.username
    )

    for attr in data:
        if hasattr(doc, attr):
            if attr == 'doc_name':
                pass    
            elif attr == 'type':
                requested_type = get_doctype_by_pubid(data.get(attr)['public_id'])
                if not requested_type:
                    raise NotFoundError(f"The requested type with ID {attr['public_id']} could not be found.")
                doc.type = requested_type
            
            else:
                setattr(doc, attr, data.get(attr))

    db.session.add(doc)
    _save_changes()

    return synth_doc(doc)


def create_doc_note(doc, content):
    """ Creates a Note for a given Doc """
    curr_user = get_request_user()
    note = DocprocNote(
        public_id = str(uuid.uuid4()),
        content = content,
        doc_id = doc.id,
        author_id = curr_user.id,
        inserted_on=datetime.datetime.utcnow(),
        updated_on=datetime.datetime.utcnow(),
    )
    db.session.add(note)
    _save_changes()

    return synth_doc(doc)


def synth_doc(doc):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    correspondence_date_format = '%Y-%m-%d'
    doc_synth = {
        'public_id': doc.public_id,
        'file_name': doc.file_name,
        'doc_name': doc.doc_name,
        'source_channel': doc.source_channel,
        'correspondence_date': doc.correspondence_date.strftime(correspondence_date_format) if doc.correspondence_date else None,
        'from_who': doc.from_who,
        'debt_name': doc.debt_name,
        'creditor_name': doc.creditor_name,
        'collector_name': doc.collector_name,
        'status': doc.status,
        'is_published': doc.is_published,
        'notes': [],
        'client': None,
        'docproc_user': None,
        'accmgr_user': None,
        'inserted_on': doc.inserted_on.strftime(datetime_format),
        'created_by_username': doc.created_by_username,
        'updated_on': doc.updated_on.strftime(datetime_format),
        'updated_by_username': doc.updated_by_username,
    }

    if doc.client_id:
        # TODO - Define what is an "Active" client and proper way to handle
        client_record = get_client_by_id(doc.client_id)
        doc_synth['client'] = {
            'public_id': client_record.public_id,
            'first_name': client_record.first_name,
            'last_name': client_record.last_name,
            'status': 'Active'
        }

    if doc.docproc_user_id:
        docproc_user_record = get_user_by_id(doc.docproc_user_id)
        doc_synth['docproc_user'] = {
            'public_id': docproc_user_record.public_id,
            'username': docproc_user_record.username
        }

    if doc.accmgr_user_id:
        accmgr_user_record = get_user_by_id(doc.accmgr_user_id)
        doc_synth['accmgr_user'] = {
            'public_id': accmgr_user_record.public_id,
            'username': accmgr_user_record.username
        }

    notes = DocprocNote.query.filter_by(doc_id=doc.id).order_by(db.desc(DocprocNote.id)).all()
    for note_item in notes:
        author_user_record = get_user_by_id(note_item.author_id)
        tmp_note = {
            'public_id': note_item.public_id,
            'content': note_item.content,
            'author': {
                'public_id': author_user_record.public_id,
                'username': author_user_record.username
            },
            'inserted_on': doc.inserted_on.strftime(datetime_format),
            'updated_on': doc.updated_on.strftime(datetime_format),
        }
        doc_synth['notes'].append(tmp_note)

    if doc.type:
        doc_synth['type'] = {
            'public_id': doc.type.public_id,
            'name': doc.type.name,
        }

    return doc_synth


def _save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()