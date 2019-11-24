import json

#######################
## Private Functions ##
#######################

from config.mysql_init import init_mysql
from config.config import *

# Basic authentication function
# Will determine whether or not this user is able to access this
# Data represents all of the post data, type represents the authentication type to validate against
def authenticate(data, type, method):
    # print("Authenticating")

    if type == "default":
        # We simply want to make sure this is not a black-listed IP address
        # And some basic authentication
        return authenticate_default(data, method)

# Default authentication
def authenticate_default(data, method):
    # print("Authenticating against default, with method of " + method)

    # Checking if we are NOT post
    # If we are NOT post, we need to get out of here
    if method == "GET":
        # print("Access failure!")
        return False

    # Checking against the black-listed IP address

    # If we are in white-listed mode, we will instead check against the white-listed IP address set
    return True

# Function that authenticates emplyoee tokens
def auth_token(employee_id, employee_auth):
    print("Authenticating employee token")

    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    auth_token_query = "SELECT employee_id FROM tb_employee WHERE employee_auth = %s AND employee_id = %s"
    cursor.execute(auth_token_query, (employee_auth, employee_id))

    result = cursor.fetchall()

    if len(result) <= 0:
        # Invalid token
        return False

    return True

# Function for authenticating a users privileges against the system
# This allows us to enforce privileges for certain access
# Access call represents what the employee is trying to do (ie: edit a user other than themselves)
# See the wiki for a full feature list
# Using hash, id, and auth to ensure the employee is who they say they are (basically)
def check_your_privilege(employee_id, access_call):
    print("Checking privileges of " + str(employee_id) + " against access call of " + str(access_call))

    # Need to make a call to the database with the employees id to get the employees access list
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    privilege_query = "SELECT employee_permission_set FROM tb_employee_permissions WHERE employee_id = %s"
    cursor.execute(privilege_query, (employee_id,))

    # Okay lets get the results
    result_primary = cursor.fetchall()
    print(result_primary)
    if (len(result_primary) > 0):
        result = json.loads(result_primary[0][0])

        # Checking if we have this access call in our privilege set
        if access_call in result and result[access_call] == 1:
            #print("Found access call of " + access_call + " within individual employee permission set ( with id of " + str(employee_id) + " )")
            return True

    ### Hmm, no direct permissions...
    ### Lets also check their group permissions!
    privilege_group_query = "SELECT tb_employee.employee_id, tb_employee.employee_permission_group_id, tb_permission_groups.* FROM tb_employee INNER JOIN tb_permission_groups WHERE tb_employee.employee_permission_group_id = group_id AND tb_employee.employee_id = 11"

    ### Ensuring our employee_id is an integer
    employee_id = int(employee_id)

    cursor.execute(privilege_group_query, (employee_id))
    result = cursor.fetchall()
    result_full = get_format_from_raw(result, cursor)

    permission_set = json.loads(result_full['group_permission_set'])

    if access_call in permission_set and permission_set[access_call] == 1:
        return True

    return False
