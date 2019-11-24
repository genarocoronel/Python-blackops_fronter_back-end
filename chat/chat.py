#### This file deals with chat messages and direct chat interaction ####
# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Employee logging
from employee.employee import employee_log

# Config
from config.mysql_init import init_mysql
from config.config import get_format_from_raw, get_format_from_raw_full, date_to_string

def send_chat(data):
    print("Getting chat data")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "channel_id", "message", "employee_name"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer", "string", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "chat_send"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get chat for chat id of " + str(json_data['channel_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get chat for chat id of " + str(json_data['channel_id']))
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    ## TODO: ADD EMPLOYEE LOGGING ON ALL REQUESTS!
    employee_log(json_data['employee_id'], "Sending an chaat with data: " + json.dumps(data))

    ## Checking if we are attempting to edit a channel that we DO NOT have access to...
    connector = init_mysql('db_chat')
    cursor = connector.cursor()

    get_channel_members = "SELECT * FROM tb_channel_members WHERE channel_id = %s AND employee_id = %s"

    # Executing
    cursor.execute(get_channel_members, (json_data['channel_id'], json_data['employee_id']))
    result_raw = cursor.fetchall()

    if len(result_raw) <= 0:
        # We are attempting to access a chat that we are NOT part of...
        # This requires additional privilege checking...
        if not check_your_privilege(json_data['employee_id'], "chat_send_other"):
            employee_log(json_data['employee_id'],
                         "Failed privilege check to get chat for chat id of " + str(json_data['channel_id']))
            return return_error(490, "Invalid privilege", "")

    # Okay if we made it this far, we are eithering getting data from a chat we ARE a part of, or we have privileges

    send_chat = "INSERT INTO tb_message (channel_id, employee_id, message_content, employee_name) " \
                "VALUES (%s, %s, %s, %s)"

    cursor.execute(send_chat, (json_data['channel_id'], json_data['employee_id'], json_data['message'], json_data['employee_name']))
    connector.commit()

    # Updating the new message value for all members in this EXCEPT for myself...
    update_chat_amount = "UPDATE tb_channel_members SET new_message = new_message + 1 WHERE employee_id != %s AND channel_id = %s"
    cursor.execute(update_chat_amount, (json_data['employee_id'], json_data['channel_id']))
    connector.commit()

    return return_success(200,"Successfully sent chat message")


def get_chat(data):
    print("Getting chat data")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "channel_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "chat_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get chat for chat id of " + str(json_data['channel_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get chat for chat id of " + str(json_data['channel_id']))
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    ## TODO: ADD EMPLOYEE LOGGING ON ALL REQUESTS!
    employee_log(json_data['employee_id'], "Getting a chaat with data: " + json.dumps(data))

    ## Checking if we are attempting to edit a channel that we DO NOT have access to...
    connector = init_mysql('db_chat')
    cursor = connector.cursor()

    get_channel_members = "SELECT * FROM tb_channel_members WHERE channel_id = %s AND employee_id = %s"

    # Executing
    cursor.execute(get_channel_members, (json_data['channel_id'],json_data['employee_id']))
    result_raw = cursor.fetchall()

    if len(result_raw) <= 0:
        # We are attempting to access a chat that we are NOT part of...
        # This requires additional privilege checking...
        if not check_your_privilege(json_data['employee_id'], "chat_get_other"):
            employee_log(json_data['employee_id'],
                         "Failed privilege check to get chat for chat id of " + str(json_data['channel_id']))
            return return_error(490, "Invalid privilege", "")

    # Okay if we made it this far, we are eithering getting data from a chat we ARE a part of, or we have privileges

    get_chat = "SELECT * FROM tb_message WHERE channel_id = %s ORDER BY message_sent_time DESC"
    cursor.execute(get_chat, (json_data['channel_id'],))
    result_raw = cursor.fetchall()

    result = get_format_from_raw_full(result_raw, cursor)

    # Performing format fix
    new_message_list = []
    for message in result:
        print(message)
        sent_time = message['message_sent_time']
        sent_time = date_to_string(sent_time)

        message['message_sent_time'] = sent_time
        new_message_list.append(message)

    # Lets also update the fact that we've read all of the messages here...
    update_chat = "UPDATE tb_channel_members SET new_message = 0 WHERE channel_id = %s AND employee_id = %s"
    cursor.execute(update_chat, (json_data['channel_id'], json_data['employee_id']))
    connector.commit()

    return return_success(200, new_message_list)