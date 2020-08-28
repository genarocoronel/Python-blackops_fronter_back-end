import os
import uuid
import time
import datetime

from werkzeug.utils import secure_filename
from flask import g, send_from_directory, after_this_request, current_app as app

from app.main.core.errors import BadRequestError, NotFoundError
from app.main.core.rac import RACRoles
from app.main.core.io import (save_file, stream_file, delete_file, generate_secure_filename, 
    get_extension_for_filename, get_mime_from_extension)
from app.main.config import upload_location
from app.main import db
from app.main.model.docproc import (DocprocChannel, DocprocType, DocprocStatus, 
    DocprocNote, Docproc)
from app.main.model.candidate_docs import CandidateDoc
from app.main.service.user_service import get_user_by_id, get_request_user
from app.main.service.client_service import get_client_by_id
from app.main.service.third_party.aws_service import (upload_to_docproc, download_from_docproc)

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


def get_docs_for_client(client):
    """ Gets all Doc to Process """
    docs = []

    doc_records = Docproc.query.filter_by(client_id=client.id).all()
        
    if doc_records:
        for doc_item in doc_records:
            tmp_doc = synth_doc(doc_item)
            docs.append(tmp_doc)
    
    return docs


def get_docs_for_portal_user():
    """ Gets Docs for current Portal User """
    docs = []
    doc_records = Docproc.query.filter_by(client_id=g.current_portal_user['client_id'], 
                                            is_published=True).all()

    if doc_records:
        for doc_item in doc_records:
            tmp_doc = synth_portal_doc(doc_item)
            docs.append(tmp_doc)

    return docs


def get_doc_by_pubid(public_id):
    """ Gets a Doc by Public ID """
    return Docproc.query.filter_by(public_id=public_id).first()


def get_doc_for_mms(mms_media):
    """ Gets a Doc for a MMS Media """
    return Docproc.query.filter_by(file_name=mms_media.file_uri, source_channel=DocprocChannel.SMS.value).first()


def get_docproc_types():
    """ Gets all known Doc Process Types """
    return DocprocType.query.filter_by().all()


def get_docproc_statuses():
    """ Gets all known Doc Process Statuses """
    statuses = [
        {'name':DocprocStatus.NEW.value}, 
        {'name':DocprocStatus.PENDING.value},
        {'name':DocprocStatus.REJECT.value},
        {'name':DocprocStatus.WAIT_AM_REVIEW.value},
        {'name':DocprocStatus.APPROVED.value},
        {'name':DocprocStatus.NEW_REJECT.value}
    ]

    return statuses


def get_doctype_by_pubid(public_id):
    """ Gets a Doc Type Public ID """
    return DocprocType.query.filter_by(public_id=public_id).first()


def get_doctype_by_name(name):
    """ Gets a Doc Type by name """
    return DocprocType.query.filter_by(name=name).first()


def multiassign_for_processing(docs_to_assign, docproc_user):
    """ Assigns Docs to a User for processing """
    docs_to_assign_synth = []
    print(f'User ID is: {docproc_user.id}')

    if docproc_user.role.name != RACRoles.DOC_PROCESS_REP.value:
        raise BadRequestError(f'Assignee user must be a member of the Doc Process Role')
    
    for doc_item in docs_to_assign:
        doc_item.docproc_user_id = docproc_user.id
        db.session.add(doc_item)
        doc_item_synth = synth_doc(doc_item)
        docs_to_assign_synth.append(doc_item_synth)

    _save_changes()

    return docs_to_assign_synth


def move_to_client_dossier(doc, client):
    """ Moves a Doc to a Client dossier """
    doc.client_id = client.id
    db.session.add(doc)
    _save_changes()

    return synth_doc(doc)


def update_doc(doc, data):
    """ Updates a Doc """
    from app.main.service.workflow import DocprocWorkflow
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

    ## creating tasks 
    dwf = DocprocWorkflow(doc)
    dwf.on_doc_update()

    return synth_doc(doc)


def allowed_doc_file_kinds(filename):
    """ Gets whether a given filename is of allowed extension for Doc Processing """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_DOC_EXTENSIONS


def attach_file_to_doc_candidate(doc, file):
    """ Attaches a File to a Candidate Doc """
    orig_filename = generate_secure_filename(file.filename)
    fileext_part = get_extension_for_filename(orig_filename)
    ms = time.time()
    unique_filename = 'docproc_{}_{}{}'.format(doc.public_id, ms, fileext_part)
    secure_filename, secure_file_path = save_file(file, unique_filename, upload_location)

    @after_this_request
    def cleanup(resp):
        # JAJ Note: Comment line below to disconnect AWS S3 feature for local-only testing
        #delete_file(secure_file_path)
        return resp

    # JAJ Note: Comment line below to disconnect AWS S3 feature for local-only testing
    #upload_to_docproc(secure_file_path, secure_filename)
    doc.file_name = secure_filename
    doc.orig_file_name = orig_filename
    db.session.add(doc)
    _save_changes()

    return synth_doc_candidate(doc)


def attach_file_to_doc(doc, file):
    """ Saves and attaches a File to a Doc """
    orig_filename = generate_secure_filename(file.filename)
    fileext_part = get_extension_for_filename(orig_filename)
    ms = time.time()
    unique_filename = 'docproc_{}_{}{}'.format(doc.public_id, ms, fileext_part)
    secure_filename, secure_file_path = save_file(file, unique_filename, upload_location)

    @after_this_request
    def cleanup(resp):
        # JAJ Note: Comment line below to disconnect AWS S3 feature for local-only testing
        delete_file(secure_file_path)
        return resp

    # JAJ Note: Comment line below to disconnect AWS S3 feature for local-only testing
    upload_to_docproc(secure_file_path, secure_filename)

    return update_doc(doc, dict(file_name=secure_filename, orig_file_name=orig_filename))


def stream_doc_file(doc, send_as_attachment=False):
    """ Streams File associated with Doc """
    file_ext = get_extension_for_filename(doc.file_name)
    mime = get_mime_from_extension(file_ext)
    filepath = os.path.join(upload_location, doc.file_name)

    @after_this_request
    def cleanup(resp):
        # JAJ Note: Comment line below to disconnect AWS S3 feature for local-only testing
        delete_file(filepath)
        return resp

    # JAJ Note: Comment line below to disconnect AWS S3 feature for local-only testing
    download_from_docproc(doc.source_channel, doc.file_name, filepath)

    return stream_file(upload_location, doc.file_name, as_attachment=send_as_attachment, mimetype=mime)


def create_doc_manual(data, client = None, return_model = False):
    """ Creates a new Doc manually """
    is_published = False
    curr_user = None
    
    if data['source_channel'] == DocprocChannel.PORTAL.value:
        is_published = True
        curr_username = 'system'
    else:
        curr_user = get_request_user()
        if curr_user:
            curr_username = curr_user.username
        else:
            curr_username = 'system'

    doc = Docproc(
        public_id = str(uuid.uuid4()),
        doc_name=data['doc_name'],
        source_channel=DocprocChannel.MAIL.value,
        status=DocprocStatus.NEW.value,
        inserted_on=datetime.datetime.utcnow(),
        created_by_username = curr_username,
        updated_on=datetime.datetime.utcnow(),
        updated_by_username=curr_username,
        is_published = is_published
    )

    if data['source_channel'] == DocprocChannel.DSTAR.value:
        doc.source_channel = DocprocChannel.DSTAR.value
        

    for attr in data:
        if hasattr(doc, attr):
            if attr == 'doc_name':
                pass    
            elif attr == 'type':
                if 'public_id' in data:
                    requested_type = get_doctype_by_pubid(data.get(attr)['public_id'])
                    if not requested_type:
                        raise NotFoundError(f"The requested type with ID {attr['public_id']} could not be found.")
                    doc.type = requested_type
                else:
                    requested_type = get_doctype_by_name('Other')
                    if not requested_type:
                        raise NotFoundError(f"The default requested type 'Other' could not be found.")
                    doc.type = requested_type
            
            else:
                setattr(doc, attr, data.get(attr))
    
    if client:
        move_to_client_dossier(doc, client)
    else:
        db.session.add(doc)
        _save_changes()
    
    if return_model:
        return doc
    else:
        return synth_doc(doc)


def create_doc_from_fax(src_file_name):
    """ Create Document from Fax comm """
    public_id = str(uuid.uuid4())

    doc = Docproc(
        public_id = public_id,
        orig_file_name=src_file_name,
        file_name=src_file_name,
        source_channel=DocprocChannel.FAX.value,
        status=DocprocStatus.NEW.value,
        inserted_on=datetime.datetime.utcnow(),
        created_by_username = 'system',
        updated_on=datetime.datetime.utcnow(),
        updated_by_username='system',
    )
    db.session.add(doc)
    _save_changes()
    
    return synth_doc(doc)


def create_doc_from_email(src_file_name):
    """ Create Document from Email comm """
    public_id = str(uuid.uuid4())

    doc = Docproc(
        public_id = public_id,
        orig_file_name=src_file_name,
        file_name=src_file_name,
        source_channel=DocprocChannel.MAIL.value,
        status=DocprocStatus.NEW.value,
        inserted_on=datetime.datetime.utcnow(),
        created_by_username = 'system',
        updated_on=datetime.datetime.utcnow(),
        updated_by_username='system',
    )
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


def create_doc_candidate(data, candidate):
    """ Creates a Doc manually for a Candidate """
    curr_user = get_request_user()
    curr_username = curr_user.username

    doc = CandidateDoc(
        public_id = str(uuid.uuid4()),
        type = 'Credit Reports',
        doc_name = data['doc_name'],
        source_channel = DocprocChannel.DSTAR.value,
        inserted_on = datetime.datetime.utcnow(),
        created_by_username = curr_username,
        updated_on = datetime.datetime.utcnow(),
        updated_by_username = curr_username,
        candidate_id = candidate.id
    )
    
    db.session.add(doc)
    _save_changes()

    return synth_doc_candidate(doc)


def get_doc_candidate_by_pubid(pub_id, should_return_model = False):
    """ Gets a Candidate Doc by public ID """
    result = None

    doc_record = CandidateDoc.query.filter_by(public_id=pub_id).first()
    if should_return_model:
        result = doc_record
    else:
        result = synth_doc_candidate(doc_record)

    return result


def get_all_docs_candidate(candidate):
    """ Gets all Docs for a Candidate """
    docs = []

    doc_records = CandidateDoc.query.filter_by(candidate_id=candidate.id).all()
    for doc_item in doc_records:
        tmp_doc = synth_doc_candidate(doc_item)
        docs.append(tmp_doc)

    return docs


def copy_docs_from_candidate(candidate, client):
    """ Copies Candidate Docs to Client dossier """
    candidate_docs = CandidateDoc.query.filter_by(candidate_id=candidate.id).all()
    if candidate_docs:
        doc_type = get_doctype_by_name('Smart Credit Report')
        for cdoc_item in candidate_docs:
            tmp_doc_data = {
                'doc_name': 'Initial 3B Credit Report',
                'source_channel': DocprocChannel.DSTAR.value,
                'debt_name': 'Multi',
                'creditor_name': 'Multi',
                'collector_name': 'Multi',
                'file_name': cdoc_item.file_name,
                'orig_file_name': cdoc_item.orig_file_name,
                'type': {'public_id': doc_type.public_id}
            }
            create_doc_manual(tmp_doc_data, client)

    return True


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
            'full_name': client_record.full_name,
            'friendly_id': client_record.friendly_id,
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


def synth_doc_candidate(doc):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    correspondence_date_format = '%Y-%m-%d'
    doc_synth = {
        'public_id': doc.public_id,
        'type': None,
        'doc_name': doc.doc_name,
        'source_channel': doc.source_channel,
        'file_name': doc.file_name,
        'inserted_on': doc.inserted_on.strftime(datetime_format),
        'created_by_username': doc.created_by_username,
        'updated_on': doc.updated_on.strftime(datetime_format),
        'updated_by_username': doc.updated_by_username,
    }

    return doc_synth


def synth_portal_doc(doc):
    """ Synthesizes Docs for Client Portal """
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
        'inserted_on': doc.inserted_on.strftime(datetime_format),
        'updated_on': doc.updated_on.strftime(datetime_format),
    }

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
