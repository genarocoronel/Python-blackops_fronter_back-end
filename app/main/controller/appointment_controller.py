from flask import request
from flask_restplus import Resource

from app.main.service.appointment_service import get_all_appointments, save_new_appointment, get_appointment
from ..util.dto import AppointmentDto

api = AppointmentDto.api
_appointment = AppointmentDto.appointment


@api.route('/')
class AppointmentList(Resource):
    @api.doc('list_of_appointments')
    @api.marshal_list_with(_appointment, envelope='data')
    def get(self):
        """ List all appointments """
        return get_all_appointments()

    @api.response(201, 'Appointment successfully created')
    @api.doc('create new appointment')
    @api.expect(_appointment, validate=True)
    def post(self):
        """ Creates new Appointment """
        data = request.json
        return save_new_appointment(data=data)


@api.route('/<public_id>')
@api.param('public_id', 'The Appointment Identifier')
@api.response(404, 'Appointment not found')
class Appointment(Resource):
    @api.doc('get appointment')
    @api.marshal_with(_appointment)
    def get(self, public_id):
        """ Get appointment with provided identifier"""
        appointment = get_appointment(public_id)
        if not appointment:
            api.abort(404)
        else:
            return appointment
