from flask import Flask, request
from flask_restplus import Resource, Api

from ..service.team import TeamService
from ..service.teamrequest_service import fetch_team_requests, filter_team_requests, update_team_request
from ..util.decorator import token_required
from ..util.dto import TeamDto

api = TeamDto.api
_team = TeamDto.team
_team_request = TeamDto.team_request


@api.route('/')
class TeamList(Resource):
    @token_required
    @api.doc('List of teams')
    @api.marshal_list_with(_team)
    def get(self):
        try:
            """ List all teams """
            svc = TeamService()
            return svc.get()
        except Exception as err:
            api.abort(500, "{}".format(str(err)))

    @token_required
    @api.doc('Create a team')
    @api.marshal_with(_team)
    def post(self):
        try:
            """ Create a team """
            data = request.json
            svc = TeamService()
            return svc.create(data)
        except Exception as err:
            api.abort(500, "{}".format(str(err)))

@api.route('/<team_id>')
@api.param('team_id', 'Team Identifier')
class TeamRecord(Resource):
    @token_required
    @api.marshal_with(_team)
    def put(self, team_id):
        """ Update team Information """
        try:
            payload = request.json
            service = TeamService()
            return service.update(team_id, payload)

        except Exception as e:
            api.abort(500, message=str(e), success=False)


@api.route('/<team_name>/requests')
@api.param('team_name', 'Team name')
class TeamRequestList(Resource):
    @token_required
    @api.doc('List of team requests for the given department')
    @api.marshal_list_with(_team_request)
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
    @api.marshal_list_with(_team_request)
    @token_required
    def get(self):
        try:
            """ Filter team requests based on field val """
            team_requests = filter_team_requests()
            return team_requests

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


@api.route('/<team_name>/requests/<req_id>')
@api.param('team_name', 'Team name')
class TeamRequestItem(Resource):
    @api.doc('get team request record by identifier')
    @api.marshal_with(_team_request)
    @token_required
    def get(self, team_name, req_id):
        try:
            """ get team request for the given id  """
            return "Sucess", 200

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


    @token_required
    @api.doc('update team request record')
    @api.marshal_with(_team_request)
    @token_required
    def put(self, team_name, req_id):
        try:
            """ Update team request record """
            data = request.json  
            return update_team_request(req_id, data)        

        except Exception as err:
            api.abort(500, "{}".format(str(err)))
  
