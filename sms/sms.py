# Tool for performing some of the SMS functionality the lending side needs
from twilio.rest import Client
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse

# Config
from config.mysql_init import init_mysql
from config.config import get_format_from_raw, get_format_from_raw_full, date_to_string

# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Variables
account_sid = "AC27a28affdf746d9c7b06788016b35c8c"
sms_auth_token = "a91db8822f78e7a928676140995290db"

#######################
## Private Functions ##
#######################

# Getting the SMS text messages that have been sent to the correct number
def sms_get(data):
    print("Recieving SMS data")

def sms_send_raw(phone_target, sms_text, employee_id):
    print("Sending an SMS to " + phone_target)

    client = Client(account_sid, sms_auth_token)

    message = client.messages.create(
        to=phone_target,
        from_="+18584139754",
        body=sms_text)

    # Saving the data into our system
    connector = init_mysql("db_sms")
    cursor = connector.cursor()

    save_inbound_sms = "INSERT INTO tb_sms_sent (sms_sender_id, sms_body, sms_sent_to) VALUES (%s, %s, %s)"
    cursor.execute(save_inbound_sms, (employee_id, sms_text, phone_target))

    connector.commit()

    print(message.sid)

def sms_send_auth(data):
    print("Sending authenticated SMS data")

    # Employee logging
    from employee.employee import employee_log

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
    access_call = "sms_send"

    # Checking for required data entries
    ### Performing auth check ###

    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to send sms authenticated")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to send sms authenticated")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    ### If server is already online, lets not do anything
    sms_send_raw(json_data['phone_number'], json_data['message'], json_data['employee_id'])

    return return_success(200, "Successfully sent the message")

# Function for recieving an SMS
def sms_recieve(data):
    print("Recieved SMS")

    # Parsing inbound...
    # Finding out what the body was...
    body_start_index = data.index("&Body=")
    body_end_index = data.index("&FromCountry=")

    body = data[(body_start_index + len("&Body=")):body_end_index]
    # Removing spaces
    body = body.replace("+"," ")

    # Getting the inbound number
    phone_start = data.index("&From=")
    phone_end = data.index("&ApiVersion=")

    phone = data[phone_start+9:phone_end]
    # print(phone)

    # Saving the data into our system
    connector = init_mysql("db_sms")
    cursor = connector.cursor()

    save_inbound_sms = "INSERT INTO tb_sms_recieved (sms_sender_phone, sms_body) VALUES (%s, %s)"
    cursor.execute(save_inbound_sms, (phone, body))

    connector.commit()

# Function for getting SMS templates
def sms_template_get(data):

    # Employee logging
    from employee.employee import employee_log

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
    access_call = "sms_template_get"

    # Checking for required data entries
    ### Performing auth check ###

    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get sms template")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get sms template")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    # Creating the connector
    connector = init_mysql("db_sms")
    cursor = connector.cursor()

    get_query = "SELECT * FROM tb_sms_template"
    cursor.execute(get_query, ())

    result_raw = cursor.fetchall()

    result = get_format_from_raw_full(result_raw, cursor)

    # Performing format fix
    new_template_list = []
    for template in result:
        sent_time = template['creation_date']
        sent_time = date_to_string(sent_time)

        template['creation_date'] = sent_time
        new_template_list.append(template)

    return return_success(200, new_template_list)

# Function for adding a new template
def sms_template_add(data):

    # Employee logging
    from employee.employee import employee_log

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "template_body", "template_title"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "sms_template_add"

    # Checking for required data entries
    ### Performing auth check ###

    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to create sms template")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to create sms template")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    # Creating the connector
    connector = init_mysql("db_sms")
    cursor = connector.cursor()

    new_template = "INSERT INTO tb_sms_template (template_body, template_title, template_creation_employee) VALUES (%s, %s, %s)"
    cursor.execute(new_template, (json_data['template_body'], json_data['template_title'], json_data['employee_id']))

    connector.commit()
    return return_success(200, "Successfully created template")