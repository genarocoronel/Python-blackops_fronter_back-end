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
from config.config import get_format_from_raw_full, date_to_string

### Functions for handling appointments

def create_appointment(data):
    print("Adding a new appointment")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "client_id", "appointment_datetime", "appointment_title"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer", "datetime", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "add_appointment"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to create appointment")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to create appointment")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Creating an appointment with data: " + json.dumps(data))


    # Checking if we are actually setting any of the reminder data
    appointment_reminder = {"sms": 0, "email": 0}
    if "appointment_reminder" in json_data:
        appointment_reminder = json_data['appointment_reminder']

    appointment_reminder = json.dumps(appointment_reminder)

    connector = init_mysql("db_appointment")
    cursor = connector.cursor()

    add_query = "INSERT INTO tb_appointment (client_id, employee_id, appointment_datetime, appointment_title, appointment_reminder) " \
                "VALUES (%s, %s, %s, %s, %s)"

    cursor.execute(add_query, (json_data['client_id'], json_data['employee_id'], json_data['appointment_datetime'], json_data['appointment_title'], appointment_reminder))
    connector.commit()

    employee_log(json_data['employee_id'], "Added an appointment")

    return return_success(200, "")


def get_appointment(data):
    print("Getting appointments")

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
    sanitize_list = ["integer", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "get_appointment"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get appointments")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get appointments")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Getting an appointment with data: " + json.dumps(data))

    connector = init_mysql("db_appointment")
    cursor = connector.cursor()

    select_query = "SELECT * FROM tb_appointment WHERE employee_id = %s"
    cursor.execute(select_query, (json_data['employee_id'],))

    result_raw = cursor.fetchall()
    result = get_format_from_raw_full(result_raw, cursor)

    # Parsing the datetime for appointment
    # Remember everything is GMT
    output_appointment_list = []
    for appointment_entry in result:
        new_appointment = appointment_entry

        init_date = appointment_entry['init_datetime']
        appointment_date = appointment_entry['appointment_datetime']

        str_init_date = date_to_string(init_date)
        str_appointment_date = date_to_string(appointment_date)

        new_appointment["init_datetime"] = str_init_date
        new_appointment["appointment_datetime"] = str_appointment_date

        reminder = json.loads(appointment_entry['appointment_reminder'])
        new_appointment['appointment_reminder'] = reminder

        output_appointment_list.append(new_appointment)

    employee_log(json_data['employee_id'], "Got all appointments")
    return return_success(200, output_appointment_list)

def edit_appointment(data):
    print("Editing an appointment")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "appointment_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "edit_appointment"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to edit appointment")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege to edit appointment")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Editing an appointment with data: " + json.dumps(data))

    edit_query = "UPDATE tb_appointment SET"
    edit_flag = False
    update_data = []
    if "appointment_datetime" in json_data:
        edit_query = edit_query + " appointment_datetime = %s,"
        edit_flag = True
        update_data.append(json_data['appointment_datetime'])

    if "appointment_status" in json_data:
        edit_query = edit_query + " appointment_status = %s,"
        edit_flag = True
        update_data.append(json_data['appointment_status'])

    if "appointment_notes" in json_data:
        edit_query = edit_query + " appointment_notes = %s,"
        edit_flag = True
        update_data.append(json_data['appointment_notes'])

    if "appointment_title" in json_data:
        edit_query = edit_query + " appointment_title = %s,"
        edit_flag = True
        update_data.append(json_data['appointment_title'])


    if not edit_flag:
        return return_error(500, "Missing input set", "")

    edit_query = edit_query[0:len(edit_query) - 1]
    edit_query = edit_query + " WHERE appointment_id = %s"

    connector = init_mysql("db_appointment")
    cursor = connector.cursor()

    update_data.append(json_data['appointment_id'])

    cursor.execute(edit_query, update_data)
    connector.commit()

    return return_success(200,"")