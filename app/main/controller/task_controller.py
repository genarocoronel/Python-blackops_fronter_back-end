from flask import Flask, request
from flask_restplus import Resource, Api

from ..service.usertask_service import UserTaskService, update_user_task
from ..service.user_service import get_request_user
from ..util.dto import TaskDto
from app.main.util.decorator import token_required

api = TaskDto.api
_task = TaskDto.user_task

@api.route('/')
class TaskList(Resource):
    @token_required
    @api.doc('List all tasks for the logged in user')
    @api.marshal_list_with(_task)
    def get(self):
        try:
            """ List all clients """
            user = get_request_user()
            if user is None:
                api.abort(404, 'User not found')

            # fetch owned tasks
            service = UserTaskService.request()
            tasks = service.list()

            return tasks

        except Exception as err:
            api.abort(500, "{}".format(str(err)))

@api.route('/filter')
class TaskFilter(Resource): 
    @api.doc('Filter the task resultset')
    @api.marshal_list_with(_task)
    def get(self):
        try:
            """ Filter user tasks based on field val """
            tasks = filter_user_tasks()
            return tasks

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


@api.route('/<task_id>')
@api.param('task_id', 'Task Identifier')
class TaskItem(Resource):
    @api.doc('get task record by identifier')
    @api.marshal_with(_task)
    def get(self, task_id):
        try:
            """ get team request for the given id  """
            return "Sucess", 200

        except Exception as err:
            api.abort(500, "{}".format(str(err)))


    @api.doc('update team request record')
    @api.marshal_with(_task)
    def put(self, task_id):
        try:
            """ Update task record """
            data = request.json  
            return update_user_task(task_id, data)        

        except Exception as err:
            api.abort(500, "{}".format(str(err)))
  
