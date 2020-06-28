from flask import Flask, request
from flask_restplus import Resource
from app.main.util.dto import TicketDto
from app.main.service.ticket_service import AssignedTickets, TicketService
from app.main.core.errors import ForbiddenError, NotFoundError
from app.main.util.decorator import token_required

api = TicketDto.api 
_ticket = TicketDto.ticket


@api.route('/')
class UserTickets(Resource):
    @api.doc('Fetches all assigned tickets for a user')
    @api.marshal_list_with(_ticket)
    @token_required
    def get(self):
        try:
            """ New support ticket """
            at = AssignedTickets()
            return at.get()
        except ForbiddenError as err:
            api.abort(403, message="Tickets fetch: {}".format(str(err)))
        except NotFoundError as err:
            api.abort(404, message="Tickets fetch: {}".format(str(err)))
        except Exception as err:
            api.abort(500, message="Tickets fetch: {}".format(str(err)))
    
@api.route('/<ticket_id>')
@api.param('ticket_id', 'Ticket Identifier')
class TicketItem(Resource):
    @api.doc('get ticket record by identifier')
    @api.marshal_with(_ticket)
    @token_required
    def get(self, ticket_id):
        try:
            """ get team request for the given id  """
            return "Sucess", 200

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


    @api.doc('update ticket record')
    @api.marshal_with(_ticket)
    @token_required
    def put(self, ticket_id):
        try:
            """ Update ticket record """
            data = request.json
            service = TicketService()
            return service.update(ticket_id, data)

        except Exception as err:
            api.abort(500, "{}".format(str(err)))
