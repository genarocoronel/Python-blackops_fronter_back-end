from flask import request
from flask_restplus import Resource

from app.main.util.decorator import (token_required, enforce_rac_required_roles)
from app.main.service.appointment_service import AppointmentService
from ..util.dto import AppointmentDto

api = AppointmentDto.api
_appointment = AppointmentDto.appointment


@api.route('/')
class AppointmentList(Resource):
    @api.doc('list_of_appointments')
    @api.marshal_list_with(_appointment, envelope='data')
    @token_required
    def get(self):
        """ List all appointments """
        return AppointmentService.list()

    @api.response(201, 'Appointment successfully created')
    @api.doc('create new appointment')
    @api.marshal_with(_appointment)
    def post(self):
        try:
            """ Creates new Appointment """
            return AppointmentService.save(request) 

        except Exception as err:
            api.abort(500, "{}".format(str(err))) 


@api.route('/<public_id>')
@api.param('public_id', 'The Appointment Identifier')
@api.response(404, 'Appointment not found')
class Appointment(Resource):
    @api.doc('get appointment')
    @api.marshal_with(_appointment)
    @token_required
    def get(self, public_id):
        try:
            """ Get appointment with provided identifier"""
            appointment = AppointmentService.get(public_id)
            return appointment
        except Exception as err:
            api.abort(500, "{}".format(str(err))) 

    @api.doc('update appointment')
    @api.marshal_with(_appointment)
    @token_required
    def put(self, public_id):
        try:
            print(public_id)
            """ Update appointment service """
            appointment = AppointmentService.update(public_id, request)
            return appointment

        except Exception as err:
            api.abort(500, "{}".format(str(err))) 
