# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Importing the employee log
from employee.employee import employee_log

# Config
from config.mysql_init import init_mysql
from config.config import encode_datetime, get_format_from_raw, get_format_from_raw_full


### Public RESTful API Calls ###
def get_calls(data):
    #### Function for getting all calls...
    print("Getting call data")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "call_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = ""
    if json_data['call_id'] == "self":
        access_call = "call_get_self"
    elif json_data['call_id'] == "all":
        access_call = "call_get_all"
    else:
        access_call = "call_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get call data on " + str(json_data['call_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get call data on " + str(json_data['call_id']))
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Get call data on " + str(json_data['call_id']))

    connector = init_mysql("db_call")
    cursor = connector.cursor()

    ### Making the call based off of our access type
    call_id = json_data['call_id']

    if call_id == "self":
        ### Getting all calls associated with ourselves
        select_query = "SELECT * FROM tb_call WHERE call_employee_id = %s"
        cursor.execute(select_query, (json_data['employee_id'],))

        result_raw = cursor.fetchall()
        result_full = get_format_from_raw_full(result_raw, cursor)
        result_full = encode_datetime(result_full)

        return return_success(200, result_full)

    elif call_id == "all":
        ### Getting ALL calls!
        select_query = "SELECT * FROM tb_call"
        cursor.execute(select_query)

        result_raw = cursor.fetchall()
        result_full = get_format_from_raw_full(result_raw, cursor)

        # As per usual, fixing datetime issues >:|
        result_full = encode_datetime(result_full)
        return return_success(200, result_full)

    elif isinstance(int, call_id):
        ### Assuming call_id is an integer value
        select_query = "SELECT * FROM tb_call WHERE call_id = %s"
        cursor.execute(select_query, (json_data['call_id'],))

        result_raw = cursor.fetchall()
        result_full = get_format_from_raw_full(result_raw, cursor)
        result_full = encode_datetime(result_full)

        return return_success(200, result_full)

    else:
        return return_error(500, "Invalid call_id", json_data['call_id'])

### Private Methods ###
def init_call_direct(data):
    print("Initializing a call from a VoIP route")

    mydb = init_mysql("db_call")
    cursor = mydb.cursor()

    insert_call = "INSERT INTO db_call.tb_call (call_inbound_number, call_employee_id, call_target_number, call_sid) VALUES (%s, %s, %s, %s)"
    cursor.execute(insert_call, (data['inbound'], data['employee_id'], data['employee_phone'], data['call_sid']))
    new_call_id = cursor.lastrowid

    ### Also updating the employee's call status (assuming its not totally screwed and broken right now, which it could be)
    select_employee_call_track = "SELECT * FROM db_employee.tb_employee_call_tracking WHERE employee_id = %s"
    cursor.execute(select_employee_call_track, (data['employee_id'],))
    result_raw = cursor.fetchall()

    if len(result_raw) <= 0:
        ### Inserting
        insert = "INSERT INTO db_employee.tb_employee_call_tracking (employee_id, call_id, call_status) VALUES (%s, %s, 1)"
        cursor.execute(insert, (data['employee_id'], new_call_id))
    else:
        ### Updating
        update = "UPDATE db_employee.tb_employee_call_tracking SET call_id = %s, call_status = 1 WHERE employee_id = %s"
        cursor.execute(update, (new_call_id, data['employee_id']))

    mydb.commit()


