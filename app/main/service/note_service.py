import uuid
from datetime import datetime
import json

from flask import current_app, jsonify
from app.main import db
from app.main.model.notes import Note

def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()

def fetch_note(author_id, candidate_id, client_id):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    notes = Note.query.filter_by(author_id=author_id, candidate_id=candidate_id,client_id=client_id).all()
    notes_data = []
    for note in notes:
        data = {
            "public_id" : note.public_id,
            "content" : note.content,
            "inserted_on" : note.inserted_on.strftime(datetime_format),
            "updated_on" : note.updated_on.strftime(datetime_format),
        }
        notes_data.append(data)
    return {"success": True, "data": notes_data}, 200

def create_note(author_id, candidate_id, client_id, content):
    datetime_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    data = {
        "public_id" : str(uuid.uuid4()),
        "author_id" : author_id,
        "candidate_id" : candidate_id,
        "client_id" : client_id,
        "content" : content,
        "inserted_on" : datetime.now(),
        "updated_on" : datetime.now(),
    }
    new_note = Note(
        public_id = data['public_id'],
        author_id = data['author_id'],
        candidate_id = data['candidate_id'],
        client_id = data['client_id'],
        content = data['content'],
        inserted_on = data['inserted_on'],
        updated_on = data['updated_on'],
    )
    data['inserted_on'] = data['inserted_on'].strftime(datetime_format)
    data['updated_on'] = data['updated_on'].strftime(datetime_format)
    save_changes(new_note)
    return {"success": True, "data": data}, 200
