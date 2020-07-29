from flask import Flask, request
from flask_restplus import Resource, Api

from app.main.util.decorator import token_required
from app.main.model.client import ClientType
from ..util.dto import NotesDto
from ..service.note_service import create_note, fetch_note
from ..service.candidate_service import get_candidate
from ..service.client_service import get_client
from ..service.user_service import get_a_user

api = NotesDto.api 
_note = NotesDto.note

@api.route('/')
class Notes(Resource):
    @api.doc('get notes for a given author')
    @token_required
    def get(self):
        try:
            author_id = request.args.get('author_id')
            candidate_id = request.args.get('candidate_id', default=None)
            client_id = request.args.get('client_id', None)
            author = get_a_user(author_id)
            if author:
                if candidate_id:
                    candidate = get_candidate(candidate_id)
                    if candidate:
                        return fetch_note(author.id, candidate.id, None)
                    return {"success": False, "message": 'Candidate not exist'}, 404
                elif client_id:
                    client = get_client(client_id, client_type=ClientType.lead)
                    if client:
                        return fetch_note(author.id, None, client.id)
                    return {"success": False, "message": 'Client not exist'}, 404   
                else:
                    response_object = {
                        'success': False,
                        'message': 'client or candidate id is required'
                    }
                    return response_object, 404
            response_object = {
                'success': False,
                'message': 'Author does not exist'
            }
            return response_object, 404

        except Exception as err:
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400

@api.route('/<public_id>')
@api.param('public_id', 'Author public identifier')
@api.response(404, 'Author not found')
class AuthorNotes(Resource):
    @api.response(200, 'Notes successfully added')
    @api.doc('Add Notes')
    @api.expect(_note, validate=True)
    @token_required
    def post(self, public_id):
        try:
            data = request.json
            author = get_a_user(public_id)
            if author:
                if data.get('candidate_id'):
                    candidate = get_candidate(data.get('candidate_id'))
                    if candidate:
                        return create_note(author.id, candidate.id, None, data.get('content'))
                    return {"success": False, "message": 'Candidate not exist'}, 404
                elif data.get('client_id'):
                    client = get_client(data.get('client_id'), client_type=ClientType.lead)
                    if client:
                        return create_note(author.id, None, client.id, data.get('content'))
                    return {"success": False, "message": 'Client not exist'}, 404
                else:
                    response_object = {
                        'success': False,
                        'message': 'client or candidate id is required'
                    }
                    return response_object, 404          

            response_object = {
                'success': False,
                'message': 'Author does not exist'
            }
            return response_object, 404

        except Exception as err:
            return {'message': 'Internal Server error - {}'.format(str(err))}, 400
