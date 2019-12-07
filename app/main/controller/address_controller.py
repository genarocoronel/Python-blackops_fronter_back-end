from flask import request
from flask_restplus import Resource

from ..util.dto import AddressDto
from app.main.service.address_service import save_new_address

api = AddressDto.api
_new_address = AddressDto.new_address


@api.route('/')
class AddressController(Resource):

    @api.response(200, 'Address successfully created')
    @api.doc('create new address')
    @api.expect(_new_address, validate=True)
    def post(self):
        #TODO: Validate candidate Id?
        """ Creates new Address """
        data = request.json
        return save_new_address(address=data)