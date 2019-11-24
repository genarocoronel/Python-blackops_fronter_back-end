#### This file deals with channel chat interaction ####
#### Primarily, seeing chats, and updating channel member lists ####
# Basic imports
import collections
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Employee logging
from employee.employee import employee_log

# Config
from config.mysql_init import init_mysql
from config.config import get_format_from_raw, get_format_from_raw_full

# Notifications
from notify.notify import notify_employee

# Function for getting all channels for an employee
def get_all_channels(json_data):
    print("Getting all channels")

    connector = init_mysql("db_chat")
    cursor = connector.cursor()

    ## Figuring which channels we are in
    get_all_channels = "SELECT channel_id FROM tb_channel_members WHERE employee_id = %s"
    cursor.execute(get_all_channels, (json_data['employee_id'],))

    results_raw = cursor.fetchall()
    results = get_format_from_raw_full(results_raw, cursor)
    full_result = []

    for channel in results:
        channel_id = channel['channel_id']

        # Getting the results for this channel
        # Okay we are getting one channel
        get_query = "SELECT * FROM tb_channel WHERE tb_channel.channel_id = %s"

        cursor.execute(get_query, (channel_id,))
        results_raw = cursor.fetchall()

        results = get_format_from_raw(results_raw, cursor)

        # Getting all of the members of this chat room
        get_employees = "SELECT * FROM tb_channel_members WHERE channel_id = %s"

        cursor.execute(get_employees, (channel_id,))
        results_raw = cursor.fetchall()

        results_employee = get_format_from_raw_full(results_raw, cursor)

        # Returning this data out
        result = {"channel": results, "members": results_employee, "channel_id": channel_id}
        full_result.append(result)

    return return_success(200, full_result)

# Function for getting one specific channel
def get_channel(data):
    print("Getting channel data")

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
    sanitize_list = ["integer", "string", "integer"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "chat_channel_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get chat channel")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get chat channel")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Getting an channel with data: " + json.dumps(data))

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    # Checking if we are getting all chats
    if "channel_id" not in json_data:
        return get_all_channels(json_data)

    # Okay we are getting one channel
    get_query = "SELECT * FROM tb_channel WHERE tb_channel.channel_id = %s"

    connector = init_mysql("db_chat")
    cursor = connector.cursor()

    cursor.execute(get_query, (json_data['channel_id'],))
    results_raw = cursor.fetchall()

    results = get_format_from_raw(results_raw, cursor)

    # Getting all of the members of this chat room
    get_employees = "SELECT * FROM tb_channel_members WHERE channel_id = %s"

    cursor.execute(get_employees, (json_data['channel_id'],))
    results_raw = cursor.fetchall()

    results_employee = get_format_from_raw_full(results_raw, cursor)

    # Returning this data out
    result = {"channel": results, "members": results_employee}
    return return_success(200, result)

# Function for adding a channel
def create_channel(data):
    print("Creating a new channel")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "channel_title"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "chat_channel_create"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to create chat channel")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to create chat channel")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Creating an channel with data: " + json.dumps(data))

    # Inserting the channel into tb_channel
    connector = init_mysql("db_chat")
    cursor = connector.cursor()

    add_new_channel = "INSERT INTO tb_channel (channel_creator, channel_title) VALUES (%s, %s)"
    cursor.execute(add_new_channel, (json_data['employee_id'], json_data['channel_title']))

    channel_id = cursor.lastrowid;

    # Inserting the tb channel members
    add_channel_member = "INSERT INTO tb_channel_members (employee_id, channel_id) VALUES (%s, %s)"
    cursor.execute(add_channel_member, (json_data['employee_id'], channel_id))

    # Inserting into the table all of the channel members that are added
    # Will skip if its the employee who created it
    insert_list = [int(json_data['employee_id'])]
    for entry in json_data['members']:

        if entry in insert_list:
            continue

        # Skipping if we have already inserted this
        add_channel_member = "INSERT INTO tb_channel_members (employee_id, channel_id) VALUES (%s, %s)"
        cursor.execute(add_channel_member, (entry, channel_id))
        insert_list.append(entry)

    connector.commit()

    # Creating all of the commits for the member list
    insert_list = [int(json_data['employee_id'])]
    for entry in json_data['members']:
        if entry in insert_list:
            continue

        notify_employee("You have joined a new chat channel", "", entry, "message_view")



    return return_success(200,"")



# Function for adding or removing members
def edit_channel(data):
    print("Editing channel")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "edit", "target_employee", "channel_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string", "integer", "integer"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "chat_channel_edit"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to edit chat channel")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to edit chat channel")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Editing an channel with data: " + json.dumps(data))

    # Checking if this is OUR channel
    # If not, we need to check if we can edit other peoples channels
    connector = init_mysql("db_chat")
    cursor = connector.cursor()

    get_channel_id = "SELECT * FROM tb_channel WHERE channel_id = %s"
    cursor.execute(get_channel_id, (json_data['channel_id'],))

    result_raw = cursor.fetchall()

    if (len(result_raw) <= 0):
        employee_log(json_data['employee_id'],
                     "Failed accessing invalid channel id")
        return return_error(490, "Invalid channel id", "")

    results = get_format_from_raw(result_raw, cursor)

    # Checking if we are the channel owner
    if (results['channel_creator'] != json_data['employee_id']):
        # Checking more privileges
        if not check_your_privilege(json_data['employee_id'], "chat_channel_edit_other"):
            employee_log(json_data['employee_id'],
                         "Failed privilege check to edit chat channel")
            return return_error(490, "Invalid privilege", "")

    # Alright checking the type now
    if json_data['edit'] == "add_employee":

        # First check if we aren't already in this channel lmao
        get_already_here = "SELECT channel_member_id FROM tb_channel_members WHERE employee_id = %s AND channel_id = %s"
        cursor.execute(get_already_here, (json_data['target_employee'], json_data['channel_id']))

        results = cursor.fetchall()
        if len(results) > 0:
            return return_error(590, "Employee already exists", "")

        # Adding an employee
        add_query = "INSERT INTO tb_channel_members (employee_id, channel_id) VALUES (%s, %s)"
        cursor.execute(add_query, (json_data['target_employee'], json_data['channel_id']))

        connector.commit()

        return return_success(200,"")

        # Alright checking the type now
    elif json_data['edit'] == "remove_employee":

            # First check if we aren't already in this channel lmao
            print("Deleting employee from channel")

            get_already_here = "SELECT channel_member_id FROM tb_channel_members WHERE employee_id = %s AND channel_id = %s"
            cursor.execute(get_already_here, (json_data['target_employee'], json_data['channel_id']))

            results = cursor.fetchall()

            if len(results) <= 0:
                return return_error(590, "Employee not part of channel", "")

            results = get_format_from_raw(results, cursor)
            channel_member_id = results['channel_member_id']

            # Adding an employee
            add_query = "DELETE FROM tb_channel_members WHERE channel_member_id = %s"
            cursor.execute(add_query, (channel_member_id,))

            connector.commit()

            return return_success(200, "")
    else:
        return return_error(590,"Invalid edit type","")

# Function for getting a chat channels member list
def get_channel_members(data):
    print("Getting channel member data")

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
    access_call = "chat_channel_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get chat channel")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get chat channel")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Getting an channel members with data: " + json.dumps(data))

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    # Getting member list
    select_query = "SELECT employee_name, employee_title FROM db_chat.tb_channel_members INNER JOIN db_employee.tb_employee WHERE channel_id = %s AND db_chat.tb_channel_members.employee_id = db_employee.tb_employee.employee_id";

    connector = init_mysql("db_chat")
    cursor = connector.cursor()

    cursor.execute(select_query, (json_data['channel_id'],))
    results_raw = cursor.fetchall()

    results = get_format_from_raw_full(results_raw, cursor)
    return return_success(200, results)

# Full edit channel
def edit_channel_full(data):
    print("Editing full channel")

    print("Editing channel")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "members", "channel_title", "channel_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string", "integer", "integer"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "chat_channel_edit"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to edit chat channel")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to edit chat channel")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Editing an channel (full) with data: " + json.dumps(data))

    ### Updating the title
    connector = init_mysql("db_chat")
    cursor = connector.cursor()

    update_query = "UPDATE db_chat.tb_channel SET channel_title = %s WHERE channel_id = %s"
    cursor.execute(update_query, (json_data['channel_title'], json_data['channel_id']))
    connector.commit()

    ### Deleting all of the updated member lists...
    ### First getting the existing member list
    get_member_query = "SELECT employee_id FROM db_chat.tb_channel_members WHERE channel_id = %s"
    cursor.execute(get_member_query, (json_data['channel_id'],))

    results_raw = cursor.fetchall()
    results = get_format_from_raw_full(results_raw, cursor)

    # Converting results into an array to be compared against member list
    old_member_list = []
    new_member_list = json_data['members']


    for entry in results:
        employee_id = entry['employee_id']
        old_member_list.append(employee_id)

    # If these are the same lets just quit lol
    if collections.Counter(old_member_list) == collections.Counter(new_member_list):
        print("Identical member list, returning now")
        return return_success(200, "")

    # We have constructed the old member list
    # We will now construct the difference

    # Constructing the new ones
    additional_member_list = []
    for entry in new_member_list:
        if entry not in old_member_list:
            additional_member_list.append(entry)

    print("New member list:")
    print(additional_member_list)

    # Constructing the list to delete from
    delete_member_list = []
    for entry in old_member_list:
        if entry not in new_member_list:
            delete_member_list.append(entry)

    print("Members to delete:")
    print(delete_member_list)

    ### First we add all of the new members
    for entry in additional_member_list:
        print("Inserting: " )
        print(entry)
        insert_query = "INSERT INTO db_chat.tb_channel_members (employee_id, channel_id) VALUES (%s,%s)"
        cursor.execute(insert_query, (entry, json_data['channel_id']))

    ### Now we delete the dudes
    for entry in delete_member_list:
        print("Deleting: " )
        print(entry)
        delete_query = "DELETE FROM db_chat.tb_channel_members WHERE employee_id = %s"
        cursor.execute(delete_query, (entry,))

    ### We done here boys
    connector.commit()

    return return_success(200, "")