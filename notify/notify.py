# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Employee logging
from employee.employee import employee_log

# SMS
from sms.sms import sms_send_raw

# Config
from config.mysql_init import init_mysql, build_edit_query
from config.config import get_format_from_raw_full, date_to_string, get_format_from_raw

# Internal function for creating a notification
def notify_employee(message, stringified_data, employee, push):
    # Creating a new notification...
    connector = init_mysql("db_notify")
    cursor = connector.cursor()

    insert = "INSERT INTO tb_notify_list (notify_message, notify_data, employee_id, notify_push) VALUES (%s, %s, %s, %s)"
    cursor.execute(insert, (message, stringified_data, employee, push))

    connector.commit()

def get_notify(data):

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "type"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer", "datetime", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "get_notify"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get notify")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get notify")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Getting notifications with data: " + json.dumps(data))

    # Checking for all notifications that we have recieved that are NOT viewed
    connector = init_mysql("db_notify")
    cursor = connector.cursor()

    ### Important that we check if we are getting a specific notification, the number of new notifications, or all
    if json_data['type'] == "id":
        # Getting by id
        get_query = "SELECT * FROM tb_notify_list WHERE notify_id = %s AND employee_id = %s"
        cursor.execute(get_query, (json_data['id'],json_data['employee_id']))

        result_raw = cursor.fetchall()
        result = get_format_from_raw_full(result_raw, cursor)
        return return_success(200, result)

    elif json_data['type'] == "all":
        # Getting all notifications
        get_query_all = "SELECT * FROM tb_notify_list WHERE employee_id = %s"
        cursor.execute(get_query_all, (json_data['employee_id'],))

        result_raw = cursor.fetchall()
        result = get_format_from_raw_full(result_raw, cursor)
        return return_success(200, result)

    elif json_data['type'] == 'update':
        # Getting new notifications
        get_query_all = "SELECT * FROM tb_notify_list WHERE employee_id = %s AND notify_view_status = 0"
        cursor.execute(get_query_all, (json_data['employee_id'],))

        result_raw = cursor.fetchall()
        notify_data = get_format_from_raw_full(result_raw, cursor)

        # Fixing all of the datetime issues...
        # Performing format fix
        notify_data_output = []
        for notify in notify_data:
            sent_time = notify['notify_date']
            sent_time = date_to_string(sent_time)

            notify['notify_date'] = sent_time
            notify_data_output.append(notify)

        # Getting new notifications
        get_query_all = "SELECT new_message, channel_id FROM db_chat.tb_channel_members WHERE employee_id = %s"
        cursor.execute(get_query_all, (json_data['employee_id'],))

        result_raw = cursor.fetchall()
        message_data = get_format_from_raw_full(result_raw, cursor)

        output = {
            "notifications": notify_data_output,
            "messages": message_data
        }

        print(output)

        return return_success(200, output)

    elif json_data['type'] == "new":
        # Getting new notifications
        get_query_all = "SELECT * FROM tb_notify_list WHERE employee_id = %s AND notify_view_status = 0"
        cursor.execute(get_query_all, (json_data['employee_id'],))

        result_raw = cursor.fetchall()
        result = get_format_from_raw_full(result_raw, cursor)

        # Fixing all of the datetime issues...
        # Performing format fix
        output_notify_list = []
        for notify in result:
            sent_time = notify['notify_date']
            sent_time = date_to_string(sent_time)

            notify['notify_date'] = sent_time
            output_notify_list.append(notify)

        return return_success(200, output_notify_list)



def view_notify(data):
    print("Updating a set of notifications to viewed")


    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "notify_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer", "datetime", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "get_notify"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get notify")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get notify")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    # Checking for all notifications that we have recieved that are NOT viewed
    connector = init_mysql("db_notify")
    cursor = connector.cursor()

    update_stmt = "UPDATE tb_notify_list SET notify_view_status = 1 WHERE notify_id = %s"
    cursor.execute(update_stmt, (json_data['notify_id'],))

    connector.commit()
    return return_success(200, "Success")

def add_notify(data):
    print("Adding a notification")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "type"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer", "datetime", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to add notify")
        return return_error(490, "Invalid authentication token", "")

    ### BOILER PLATE END ###
