# Importing libraries for use
# Importing flask
from bottle import Bottle, request

######################
## Authents Imports ##
######################
from auth.auth import authenticate

######################
## Employee Imports ##
######################
from .employee import *
from .group import *

def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

def employee_load(app):
    @app.route('/employee/login', method='POST')
    def employee_login():
        # Authenticating
        authenticate_default()

        # Loading the login with the post data
        return login(request.body.read())

    @app.route('/employee/password', method='POST')
    def update_employee_password():
        # Auth
        print("HELLO")
        authenticate_default()

        return updatePassword(request.body.read())

    @app.route('/employee/get', method='POST')
    def employee_get():
        # Authenticating
        authenticate_default()

        # Loading the employees data from the system
        return get(request.body.read())

    @app.route('/employee/disable', method='POST')
    def employee_disable():
        # Authenticating
        authenticate_default()

        # Setting the employees data, given a set of data to adjust
        return disable_account(request.body.read())

    @app.route('/employee/edit', method='POST')
    @app.route('/employee/set', method='POST')
    def employee_set():
        # Authenticating
        authenticate_default()

        # Setting the employees data, given a set of data to adjust
        return edit(request.body.read())

    @app.route('/employee/edit/permission', method='POST')
    def employee_edit_permission():
        authenticate_default()

        return edit_permission(request.body.read())

    @app.route('/employee/create', method='POST')
    def employee_create():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return create(request.body.read())

    @app.route('/employee/status/set', method='POST')
    def status_set_employee():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return status_set(request.body.read())

    @app.route('/employee/group/add', method='POST')
    def employee_group_set():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return group_add(request.body.read())

    @app.route('/employee/group/update', method='POST')
    def employee_group_update():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return group_edit(request.body.read())

    @app.route('/employee/group/set', method='POST')
    def employee_group_set():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return group_user_set(request.body.read())

    @app.route('/employee/group/get', method='POST')
    def employee_group_get():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return group_get(request.body.read())

    @app.route('/employee/group/delete', method='POST')
    def employee_group_get():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return group_delete(request.body.read())

    @app.route('/permission/default', method='POST')
    def get_permission_default():
        # Authenticating
        authenticate_default()

        # Creating a new employee!
        return get_default_permissions(request.body.read())
