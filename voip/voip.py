# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Employee logging
from employee.employee import employee_log

# Tools
from tools.employee import *
from tools.calls import *
from call.call import *
from notify.notify import *

# SMS
from sms.sms import sms_send_raw

# VOIP
from twilio.twiml.voice_response import Dial, VoiceResponse, Say

# Config
from config.mysql_init import init_mysql, build_edit_query
from config.config import get_format_from_raw_full, date_to_string, get_format_from_raw

## Primary function for 'initializing' a new lead into our system!
def voip_route(data):
    print("Generating voip route!")

    ### Getting the call ID from the datapoint...
    inbound_phone = get_inbound_call_number(data)
    call_sid = get_call_sid(data)

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = {}

    ### First we need to initiailize this lead from init
    ### Obviously, need to check if this person even exists first...
    employee_route_id = get_next_available_employee()

    ### Getting that employees phone data
    route_phone = get_phone_from_employee_id(employee_route_id)

    ### Now that we've determined the employee, lets transfer the call and update our database
    json_data['employee_id'] = employee_route_id
    json_data['employee_phone'] = route_phone
    json_data['inbound'] = inbound_phone
    json_data['call_sid'] = call_sid
    init_call_direct(json_data)

    # Determining what data to return
    output = {'route': route_phone}

    ### Notifying the employee
    notify_employee("Inbound call", "{\"number\": "+json_data['inbound']+ "}", json_data['employee_id'], "inbound_call")

    return output

def voip_status_callback(data):
    print("Recieved status callback!")
    print(data)

    ### We are extremely likely just terminating the call, which is exactly what we will do!
    ### Lets look up this call first...
    call_sid = get_call_sid(data)

    connector = init_mysql("db_call")
    cursor = connector.cursor()

    select_call = "SELECT * FROM db_call.tb_call WHERE call_sid = %s"
    cursor.execute(select_call, (call_sid,))

    result = cursor.fetchall()
    print(result)

    ### Lets check what type of call this is...
    ### If it is a transfer, we do NOT want to hang up, but instead want to re-dial

    ### TODO: If live transfer, do NOT hangup...
    ### Do this by checking the results from above, check for a call status of 2 that has a live transfer enabled
    call_hangup(data)

def call_hangup(data):

    call_sid = get_call_sid(data)
    ### Ending a call, and updating our system database to match that...

    ### Updating based off of call_sid
    connector = init_mysql("db_call")
    cursor = connector.cursor()

    ### First, getting this calls ID so we can update it in the employee call as well...
    end_call_get = "SELECT call_id FROM tb_call WHERE call_sid = %s"
    cursor.execute(end_call_get, (call_sid,))
    call_id = cursor.fetchall()[0][0]

    end_call = "UPDATE tb_call SET call_status = 0, call_end = NOW() WHERE call_sid = %s"
    cursor.execute(end_call, (call_sid,))

    ### Updating it in the user call sheet as well
    end_call_employee = "UPDATE db_employee.tb_employee_call_tracking SET call_status = 0 WHERE call_id = %s"
    cursor.execute(end_call_employee, (call_id,))
    connector.commit()

    response = VoiceResponse()
    response.hangup()

    print(response)

def voip_inbound(data):

    # Using our recieved data to determine the path
    # Getting the routeable number
    route_number = voip_route(data)['route']

    response = VoiceResponse()
    response.say('Directing your call')
    response.dial('858-668-6091')
    return response.to_xml()