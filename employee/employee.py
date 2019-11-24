# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# SMS
from sms.sms import sms_send_raw

# Config
from config.mysql_init import init_mysql
from config.config import get_format_from_raw, get_format_from_raw_full


# Function that will take an access token and a set of passwords and udpate that users password
def updatePassword(data):
    # Grabbing our data
    print("Attempting user update password")

    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["token", "password", "username"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Okay lets set the hashed value to the password...
    # Updating the database...
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    update_query = "UPDATE tb_employee SET employee_password_reset_token = %s, employee_hash = %s WHERE employee_password_reset_token = %s AND employee_username = %s"
    invalid_token = random_digit(32)
    user_password = json_data['password']
    execute_data = (invalid_token, user_password, json_data['token'], json_data['username'])
    cursor.execute(update_query, execute_data)

    print("Executed!")
    print(execute_data)

    connector.commit()

# Function used for handling logins
def login(data):
    #print("Attempting to login")
    #print(data)

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["username", "password"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["string","string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Okay now we are logging in
    # Performing the MySQL connection
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    select_query = ("SELECT * from tb_employee WHERE employee_username = %s AND employee_hash = %s ")
    cursor.execute(select_query, (json_data['username'], json_data['password']))
    result_raw = cursor.fetchall()

    # Checking if we got any data
    if (len(result_raw) != 1):
        return return_error(580, "Invalid credentials", "")

    # Parsing the data
    result = [dict(line) for line in [zip([column[0] for column in cursor.description], row) for row in result_raw]][0]

    # TODO: Check for locked account
    if (result['account_lock'] == 1):
        return return_error(599, "Account is locked", "")

    # Okay if we have made it this far, we have a valid account!
    # Checking to see if we have 2fa enabled AND we are using a new IP
    # If so, we need to trigger the 2fa process
    # Checking our IP address logs for this account
    select_ip_log = ("SELECT * from tb_employee_ip_logging WHERE employee_id = %s")

    cursor.execute(select_ip_log, (result['employee_id'],))

    # Parsing output
    result_ip_raw = cursor.fetchall()

    # Flag for if we have an IP address
    no_ip = False

    if len(result_ip_raw) <= 0:
        # We do NOT have any IP address currently associated...
        no_ip = True

    else:
        # Time to search through every list within our output

        # Grabbing the IP
        client_ip = request.environ.get('REMOTE_ADDR')
        print("Inbound IP" + str(client_ip))

        result_ip = [dict(line) for line in [zip([column[0] for column in cursor.description], row) for row in result_ip_raw]]
        found_flag = False
        for ip in result_ip:
            if ip['employee_ip_log'] == client_ip:
                found_flag = True
                break

        if not found_flag:
            no_ip = True

    # Okay lets see if we have a matching IP address...
    require_2fa = result['enabled_2fa']

    if (require_2fa and no_ip):
        # Triggering 2fa
        print("Triggering 2fa")
        employee_log(result['employee_id'], "User triggered 2fa process")

        # Did the user give us a 2fa code?
        invalid_2fa = True
        if "2fa_code" in json_data:
            # Hey user gave us a 2fa code
            employee_log(result['employee_id'], "User gave 2fa code")

            # Lets check if is the most recent against the correct ip...
            if (verify_2fa(result['employee_id'], json_data['2fa_code'])):
                # Correct!
                invalid_2fa = False

        if invalid_2fa:
            # Okay lets insert a new 2fa token into our system
            code = generate_new_2fa_token(result['employee_id'], result['employee_phone_number'])

            # Texting this code
            sms_send_raw(result['employee_phone_number'],str(code) + " is your Verification Code", result['employee_id']);
            phone_number = result['employee_phone_number'];
            last_four = phone_number[len(phone_number)-4:]

            return return_success(201, {"reason": "two factor authentication required", "phone_number": last_four})

    # Otherwise, we logged in successfully!

    # Closing
    connector.close()


    new_hash = gen_new_token(result['employee_id'], result['employee_username'], result['employee_hash'])
    return_result = {"employee_id": result['employee_id'], "employee_auth": new_hash, "employee_name": result['employee_name'], "employee_username": result['employee_username']}

    employee_log(result['employee_id'], "User logged in")

    ### Now that the employee has logged in, lets update the status of the employee
    status_data = {
        "employee_id": result['employee_id'],
        "employee_auth": new_hash,
        "employee_status": "active"
    }
    status_set(json.dumps(status_data))

    print("Returning result!")
    print(return_result)
    return return_success(200, return_result)


# Function for creating a new employee
def create(data):
    # print("Creating employee from data")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["name", "username", "password", "employee_2fa", "employee_phone_number"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["string", "string", "string", "string", "phone"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    ### Performing Permissions Check ###

    # Now we are going to build our authentication hash
    auth_key = generate_hash()

    # We have all of the data that we need to build an employee
    # So we will build our employee
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    sms_code = random_digit(6)

    insert_query = "INSERT INTO tb_employee (employee_password_reset_token, employee_name, employee_username, employee_hash, employee_auth, enabled_2fa, employee_phone_number, employee_title, employee_phone_route, employee_email, employee_permission_group_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(insert_query, (sms_code, json_data['name'], json_data['username'], json_data['password'], auth_key.hexdigest(), json_data['employee_2fa'], json_data['employee_phone_number'], json_data['employee_title'], json_data['employee_phone_route'], json_data['employee_email'], json_data['employee_permission_group_id']))


    # Sending an auth
    sms_message = str(sms_code) + " is your account creation code, " + str(json_data['username'] + " is your username. Thank you for signing up with EliteTesting!")
    sms_send_raw(json_data['employee_phone_number'], sms_message, -1)

    # Committing
    connector.commit()
    connector.close()

    # Building the employee permission set
    employee_id = cursor.lastrowid
    build_permission_set(employee_id)
    token = gen_new_token(employee_id, json_data['username'], json_data['password'])

    # Finally, returning the users authentication information
    return_result = {"token": token, "employee_id": employee_id}
    return return_success(200, return_result)

# Function for updating the status of an employee
def status_set(data):
    print("Setting employee status")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "employee_status"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to update status of employee data on " + str(json_data['employee_id']))
        return return_error(490, "Invalid authentication token", "")

    ### End Boilerplate ###

    # Updating the status
    status = json_data['employee_status']

    mydb = init_mysql("db_employee")
    cursor = mydb.cursor()

    ### First checking to see if we don't already have a status...
    get_status = "SELECT * FROM tb_employee_status WHERE employee_id = %s"
    cursor.execute(get_status, (json_data['employee_id'],))
    result_raw = cursor.fetchall()
    print(result_raw)

    if (len(result_raw) <= 0):
        print("Generating a new insert...")
        insert = "INSERT INTO tb_employee_status (employee_id, employee_status) VALUES (%s, %s)"
        cursor.execute(insert, (json_data['employee_id'], json_data['employee_status']))

        mydb.commit()
    else:
        print("Updating insert")

        insert = "UPDATE tb_employee_status SET employee_status = %s WHERE employee_id = %s"
        cursor.execute(insert, (json_data['employee_status'],json_data['employee_id']))

        mydb.commit()

# Function for getting employee data
def get(data):
    print("Getting employee data")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "target_employee_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = ""
    if json_data['employee_id'] == json_data['target_employee_id']:
        access_call = "employee_get_self"
    else:
        access_call = "employee_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'], "Failed auth check to get employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to get employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    employee_log(json_data['employee_id'], "Get employee data on " + str(json_data['target_employee_id']))

    connector = init_mysql("db_employee")
    cursor = connector.cursor()


    # Seeing if we are going to get all
    if json_data['target_employee_id'] == "All":
        get_query = "SELECT employee_permission_group_id, employee_username, employee_phone_route, enabled_2fa, account_lock, employee_name, employee_id, employee_title, employee_email, employee_phone_number FROM tb_employee WHERE account_lock = 0"
        cursor.execute(get_query, ())

        result_raw = cursor.fetchall()
        result = get_format_from_raw_full(result_raw, cursor)
        return return_success(200, result)

    else:
        get_query = "SELECT employee_permission_group_id, employee_username, employee_phone_route, enabled_2fa, account_lock, employee_name, employee_id, employee_title, employee_email, employee_phone_number FROM tb_employee WHERE employee_id = %s AND account_lock = 0"
        cursor.execute(get_query, (json_data['target_employee_id'],))

        result_raw = cursor.fetchall()
        result = get_format_from_raw(result_raw, cursor)

        ## Also getting the privileges
        get_priv_query = "SELECT employee_permission_set FROM tb_employee_permissions WHERE employee_id = %s"
        cursor.execute(get_priv_query, (json_data['employee_id'],))

        privilege_set = json.loads(cursor.fetchall()[0][0])
        result['employee_privilege_set'] = privilege_set

        get_group_query = "SELECT group_permission_set FROM tb_permission_groups WHERE group_id = %s"
        cursor.execute(get_group_query, (result['employee_permission_group_id'],))

        privilege_set = json.loads(cursor.fetchall()[0][0])
        result['group_privilege_set'] = privilege_set


        return return_success(200, result)


# Function for editing employee permissions set
def edit_permission(data):
    print("Editting employee permission data")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["edit"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["json"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = ""
    if json_data['employee_id'] == json_data['target_employee_id']:
        access_call = "employee_edit_permission_self"
    else:
        access_call = "employee_edit_permission"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'], "Failed auth check to edit permission employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to edit permission employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid privilege", "")

    # Making the edit
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    update_query = "UPDATE tb_employee_permissions SET employee_permission_set = %s WHERE employee_id = %s"
    cursor.execute(update_query, (json.dumps(json_data['edit']), json_data['target_employee_id']))

    connector.commit()

    return return_success(200,"")

# Function for editing employee data
def edit(data):
    print("Editting employee data")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "target_employee_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = ""
    if json_data['employee_id'] == json_data['target_employee_id']:
        access_call = "employee_edit_self"
    else:
        access_call = "employee_edit"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'], "Failed auth check to edit employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'], "Failed privilege check to edit employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    employee_log(json_data['employee_id'], "Edit employee data on " + str(json_data['target_employee_id']) + " with edit data of " + str(json_data))

    ### Building the query from what we want to edit
    edit_json = json_data['edit']

    ## Now making the update
    update_query_set = []

    query_edit = "UPDATE tb_employee SET "
    for key in edit_json:
        query_edit = query_edit + key + " = %s, "
        update_query_set.append(edit_json[key])

    # Removing last comma
    query_edit = query_edit[0:len(query_edit) - 2]

    # Finishing
    query_edit = query_edit + " WHERE employee_id = %s"

    ## Adding auth
    update_query_set.append(json_data["target_employee_id"])

    connector = init_mysql("db_employee")
    cursor = connector.cursor()
    cursor.execute(query_edit, update_query_set)

    connector.commit()

    return return_success(200,"")

def disable_account(data):

    print("Editting employee data")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "target_employee_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = ""
    if json_data['employee_id'] == json_data['target_employee_id']:
        access_call = "employee_edit_self"
    else:
        access_call = "employee_disable"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to disable employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to disable employee data on " + str(json_data['target_employee_id']))
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    update = "UPDATE tb_employee SET account_lock = 1 WHERE employee_id = %s"

    cursor.execute(update, (json_data['target_employee_id'],))
    connector.commit()

    return return_success(200, "")


#######################
## Private Functions ##
#######################


# Helper function for updating the authentication token of an employee
def gen_new_token(employee_id, employee_username, employee_hash):
    print("Generating a new token")

    new_token = generate_hash().hexdigest()
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    update_query = "UPDATE tb_employee SET employee_auth = %s WHERE employee_id = %s AND employee_username = %s AND employee_hash = %s"
    cursor.execute(update_query, (new_token, employee_id, employee_username, employee_hash))

    connector.commit()

    employee_log(employee_id, "Generated a new token")

    return new_token


# Helper function for building the employee permission set
def build_permission_set(employee_id):
    print("Building permissions set")

    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    insert_query = "INSERT INTO tb_employee_permissions (employee_id) VALUES (%s)"
    cursor.execute(insert_query, (employee_id,))

    connector.commit()

    employee_log(employee_id, "Built permissions set")


# Function for logging things when we want to log things
def employee_log(employee_id, message):
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    insert_query = "INSERT INTO tb_employee_log (employee_id, log_message) VALUES (%s, %s)"
    cursor.execute(insert_query, (employee_id, message))

    connector.commit()

    update_employee_activity(employee_id)


# Function for generating a new SMS 2fa
def generate_new_2fa_token(employee_id, employee_phone_number):
    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    message = random_digit(6)

    insert_query = "INSERT INTO tb_employee_2fa_logging (employee_id, code, ip) VALUES (%s, %s, %s)"
    cursor.execute(insert_query, (employee_id, message, client_ip))

    connector.commit()
    return message


def verify_2fa(employee_id, code):
    # Checking if the given code matches the most recent 2fa
    print("Verifying 2fa")

    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    select_query = "SELECT * FROM tb_employee_2fa_logging WHERE employee_id = %s ORDER BY date DESC LIMIT 1;"
    cursor.execute(select_query, (employee_id,))

    result_raw = cursor.fetchall()
    result = [dict(line) for line in [zip([column[0] for column in cursor.description], row) for row in result_raw]][0]

    # Comparing the code value in the system against the result
    if result["code"] == code:

        # Accurate code!
        # Associating the given IP into the system
        update_ip = "INSERT INTO tb_employee_ip_logging (employee_id, employee_ip_log) VALUES (%s, %s)"
        cursor.execute(update_ip, (employee_id, result["ip"]))

        connector.commit()

        # Returning true
        return True

    return False

### Minor function for updating employee activity...
def update_employee_activity(employee_id):
    mydb = init_mysql("db_employee")
    cursor = mydb.cursor()

    ### First checking to see if we don't already have a status...
    get_status = "SELECT * FROM tb_employee_activity_log WHERE employee_id = %s"
    cursor.execute(get_status, (employee_id,))
    result_raw = cursor.fetchall()
    print(result_raw)

    if (len(result_raw) <= 0):
        print("Generating a new insert...")
        insert = "INSERT INTO tb_employee_activity_log (employee_id, last_update) VALUES (%s, NOW())"
        cursor.execute(insert, (employee_id, ))

        mydb.commit()
    else:
        print("Updating insert")

        insert = "UPDATE tb_employee_activity_log SET last_update = NOW() WHERE employee_id = %s"
        cursor.execute(insert, (employee_id, ))

        mydb.commit()