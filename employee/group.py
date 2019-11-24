### File for dealing with permission groups
# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Employee logging
from .employee import *
from config.config import *

# SMS
from sms.sms import sms_send_raw

# Config
from config.mysql_init import init_mysql
from config.config import get_format_from_raw, get_format_from_raw_full

def group_get(data):
    ### Function for getting all of the permission groups...
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["json"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "permission_group_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get permission group data on")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to get permission group data on")
        return return_error(490, "Invalid privilege", "")

    ### Okay lets get all of the groups and return them...
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    select_group = "SELECT * FROM db_employee.tb_permission_groups"

    ### Fixing datetime problems

    cursor.execute(select_group)
    result = cursor.fetchall()
    result_full = get_format_from_raw_full(result, cursor)
    result_final = encode_datetime(result_full)

    ### Fixing the encoded group permission set
    new_output_set = []
    for output in result_final:
        new_output = output
        tmp_perm_set = json.loads(output['group_permission_set'])
        new_output['group_permission_set'] = tmp_perm_set

        new_output_set.append(new_output)

    ### Returning
    return return_success(200, new_output_set)

def group_add(data):
    ### Function for adding a new permissions group
    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "group_name", "group_permission_set"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["json"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "permission_group_add"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to add permission group data on")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to add permission group data on")
        return return_error(490, "Invalid privilege", "")

    ### Inserting the data into our system
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    ### Converting to encapsulated string
    json_group_permission = json.dumps(json_data['group_permission_set'])


    insert = "INSERT INTO db_employee.tb_permission_groups (group_name, group_permission_set) VALUES (%s, %s)"
    cursor.execute(insert, (json_data['group_name'], json_group_permission))

    connector.commit()

    return return_success(200,"")

def group_delete(data):
    ### Function for deleting a permissions group
    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "group_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["json"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "permission_group_delete"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to delete permission group data")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to delete permission group data")
        return return_error(490, "Invalid privilege", "")

    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    delete = "DELETE FROM db_employee.tb_permission_groups WHERE group_id = %s"
    cursor.execute(delete, (json_data['group_id'], ))

    connector.commit()
    return return_success(200, "")

def group_edit(data):
    ### Function for adding a new permissions group
    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "group_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["json"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "permission_group_edit"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to edit permission employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to edit permission employee data on " + str(
            json_data['target_employee_id']))
        return return_error(490, "Invalid privilege", "")

    ### Inserting the data into our system
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    ### Converting to encapsulated string
    json_group_permission = json.dumps(json_data['group_permission_set'])


    insert = "UPDATE tb_permission_groups SET group_permission_set = %s, group_name = %s WHERE group_id = %s"
    cursor.execute(insert, (json_group_permission, json_data['group_name'], json_data['group_id']))

    connector.commit()

    return return_success(200,"")


def group_user_set(data):
    ### Function for setting a new permissions group
    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "group_id", "target_employee_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["json"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "permission_group_employee_set"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to edit permission employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to edit permission employee data on " + str(
            json_data['target_employee_id']))
        return return_error(490, "Invalid privilege", "")

    ### Making edits
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    group_set = "UPDATE tb_employee SET employee_permission_group_id = %s WHERE employee_id = %s"
    cursor.execute(group_set, (json_data['group_id'], json_data['employee_id']))

    connector.commit()

    return return_success(200, "")

def get_default_permissions(data):
    ### Function for setting a new permissions group
    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["json"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "permission_default_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get permission default data")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to get permission default data")
        return return_error(490, "Invalid privilege", "")

    ### Getting permission set
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    get_default_permission = "SELECT permission_set FROM tb_default_permission_set WHERE init_key = 1"
    cursor.execute(get_default_permission)
    result = json.loads(cursor.fetchall()[0][0])

    return return_success(200, result)