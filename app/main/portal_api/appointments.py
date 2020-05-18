from flask_restplus import Resource

from app.main.util.portal_dto import AppointmentDto
from app.main.util.decorator import portal_token_required
from app.main.service.appointment_service import AppointmentService

api = AppointmentDto.api
_appointment = AppointmentDto.appointment

@api.route('/')
class ClientAppointments(Resource):
    @api.doc('Get Appointments')
    @api.marshal_list_with(_appointment, envelope='data')
    @portal_token_required
    def get(self):
        """ Gets Appointments """
        appointments = AppointmentService.list()

        return appointments, 200
