from flask import Flask, request
from flask_restplus import Resource, Api

from ..service.team_service import fetch_team_requests, filter_team_requests, update_team_request
from ..util.decorator import token_required
from ..util.dto import TeamDto

api = TeamDto.api
_team_request = TeamDto.team_request

@api.route('/<team_name>/requests')
@api.param('team_name', 'Team name')
class TeamRequestList(Resource):
    @token_required
    @api.doc('List of team requests for the given department')
    @api.marshal_list_with(_team_request, envelope='data')
    def get(self, team_name):
        try:
            """ List all clients """
            team_requests = fetch_team_requests(team_name)
            return team_requests

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


@api.route('/filter')
class TeamRequestFilter(Resource): 
    @api.doc('Filter the team requests')
    @api.marshal_list_with(_team_request, envelope='data')
    def get(self):
        try:
            """ Filter team requests based on field val """
            team_requests = filter_team_requests()
            return team_requests

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


@api.route('/<team_name>/requests/<req_id>')
@api.param('team_name', 'Team nam')
class TeamRequestItem(Resource):
    @api.doc('get team request record by identifier')
    @api.marshal_with(_team_request)
    def get(self, team_name, req_id):
        try:
            """ get team request for the given id  """
            return "Sucess", 200

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


    @token_required
    @api.doc('update team request record')
    @api.marshal_with(_team_request)
    def put(self, team_name, req_id):
        try:
            """ Update team request record """
            data = request.json  
            return update_team_request(req_id, data)        

        except Exception as err:
            api.abort(500, "{}".format(str(err)))
  
