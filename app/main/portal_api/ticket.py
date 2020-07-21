from flask_restplus import Resource
from flask import request
from app.main.util.dto import TicketDto
from app.main.service.ticket_service import PortalNewTicket, PortalOpenedTickets
from app.main.core.errors import ForbiddenError, NotFoundError
from app.main.util.decorator import portal_token_required

api = TicketDto.api 
_ticket = TicketDto.ticket


@api.route('/')
class PortalTickets(Resource):
    @api.doc('Create a support ticket')
    @api.marshal_with(_ticket)
    @portal_token_required
    def put(self):
        try:
            """ New support ticket """
            data = request.json
            pnt = PortalNewTicket()
            return pnt.open(data) 
        except ForbiddenError as err:
            api.abort(403, message="Ticket open issue: {}".format(str(err)))
        except NotFoundError as err:
            api.abort(404, message="Ticket open issue: {}".format(str(err)))
        except Exception as err:
            api.abort(500, message="Ticket open issue: {}".format(str(err)))

    @api.doc('Fetches all opened tickets by a client')
    @api.marshal_list_with(_ticket)
    @portal_token_required
    def get(self):
        try:
            """ Fetches all submitted tickets """
            pot = PortalOpenedTickets()
            return pot.get()
        except ForbiddenError as err:
            api.abort(403, message="Tickets fetch: {}".format(str(err)))
        except NotFoundError as err:
            api.abort(404, message="Tickets fetch: {}".format(str(err)))
        except Exception as err:
            api.abort(500, message="Tickets fetch: {}".format(str(err)))
    

