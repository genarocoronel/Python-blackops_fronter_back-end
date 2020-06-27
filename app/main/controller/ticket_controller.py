from flask_restplus import Resource
from app.main.util.dto import TicketDto
from app.main.service.ticket_service import AssignedTickets
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
    

