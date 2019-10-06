### Lead management file ###
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
from config.config import get_format_from_raw_full, date_to_string, get_format_from_raw, encode_datetime

def add_lead_single(data):
    print("Adding a single lead into the system")

def edit_lead(data):
    print("Editing a lead")

def get_lead_all(data):
    print("Getting leads")

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
    access_call = "get_lead"
    if 'type' in json_data and json_data['type'] == 'all':
        print("Getting all leads!")
        access_call = "get_lead_all"

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

    print("Loading leads")

    ### Getting all of the leads that this employee is responsible for (if our type is all)
    ### Are we getting all?

    mydb = init_mysql("db_lead")
    cursor = mydb.cursor()

    if access_call == "get_lead_all":
        select_statement = "SELECT * FROM db_lead.tb_lead"
        cursor.execute(select_statement, ())
        result_raw = cursor.fetchall()

    else:
        select_statement = "SELECT * FROM db_lead.tb_lead"
        cursor.execute(select_statement)
        result_raw = cursor.fetchall()

    result = get_format_from_raw_full(result_raw, cursor)

    ### Fixing datetime problems
    result_encoded = encode_datetime(result)

    return return_success(200, result_encoded)

def get_lead(data):
    print("Getting leads")

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
    access_call = "get_lead"
    if 'type' in json_data and json_data['type'] == 'all':
        print("Getting all leads!")
        access_call = "get_lead_all"

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

    print("Loading leads")

    ### Getting all of the leads that this employee is responsible for (if our type is all)
    ### Are we getting all?

    mydb = init_mysql("db_lead")
    cursor = mydb.cursor()

    if access_call == "get_lead_all":
        select_statement = "SELECT * FROM db_lead.tb_lead"
        cursor.execute(select_statement, ())
        result_raw = cursor.fetchall()

    else:
        select_statement = "SELECT * FROM db_lead.tb_lead WHERE employee_id = %s"
        cursor.execute(select_statement)
        result_raw = cursor.fetchall()

    result = get_format_from_raw_full(result_raw, cursor)

    ### Fixing datetime problems
    result_encoded = encode_datetime(result)

    return return_success(200, result_encoded)

def load_lead_from_init(data):
    print("Loading a lead directly from the init database!")

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "lead_id"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string", "integer", "datetime", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "lead_load_id"

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

    ### Building the connector and cursor
    connector = init_mysql("db_lead")
    cursor = connector.cursor()

    ### This is a fairly important and complex process...
    ### First, we need to check if the ID exists in the already loaded database
    ### If it does, error out here...
    SELECT_IF_ID_EXISTS = "SELECT * FROM tb_lead WHERE lead_id = %s"
    cursor.execute(SELECT_IF_ID_EXISTS, (json_data['lead_id'],))
    result_raw = cursor.fetchall()

    if (len(result_raw) > 0):

        ### Does exist
        result_full = get_format_from_raw_full(result_raw, cursor)[0]
        return return_error(500, "Lead already exists and has been loaded into the system", result_full)

    ### Secondly, we need to double check that this ID has not already been initialized AND it exists
    ### We do this by selecting all of the data for this within the init databsae, and seeing if it has been 'flagged'
    ### This flag indiciates if someone has ALREADY loaded the prequal number into the system
    ### And will stay flagged for the next 9 months (or whenever the system decides we want to try again)
    SELECT_ID_IF_EXIST_AND_AVAILABLE = "SELECT * FROM tb_init_lead WHERE lead_id = %s"
    cursor.execute(SELECT_ID_IF_EXIST_AND_AVAILABLE, (json_data['lead_id'],))
    result_raw = cursor.fetchall()
    result_full = encode_datetime(get_format_from_raw_full(result_raw, cursor))[0]

    if (len(result_raw) < 0):
        ### Does exist
        return return_error(500, "Lead ID does not exist", "")

    ### Checking the lead status
    lead_init_status = result_full['lead_init_status']
    if lead_init_status != 0:
        return return_error(500, "Lead already initialized", result_full)

    ### Okay, so this ID exists, is not flagged, and we have gotten the data
    ### All we need to do now is create an entry within the leads table and then return this leads data
    ### Finally, we will update the entry within the init database to show we have already access this person

    UPDATE_STATUS_TO_LOADED = "UPDATE tb_init_lead SET lead_init_status = 1 WHERE lead_id = %s"
    cursor.execute(UPDATE_STATUS_TO_LOADED, (json_data['lead_id'],))

    ### Inserting this lead into the system...
    INSERT_LEAD = "INSERT INTO tb_lead (lead_id, employee_id, lead_ident, lead_first_name, lead_middile_initial, lead_last_name, lead_dob, lead_address, lead_magic_number, lead_age, lead_suffix, lead_city, lead_state, lead_zip, lead_zip4, lead_crrt, lead_dpbc, lead_fips, lead_est_debt)" \
                  "VALUES" \
                  "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(INSERT_LEAD,
                   (
                        json_data['lead_id'],
                       json_data['employee_id'],
                       0,
                       result_full['lead_fname'],
                       result_full['lead_mi'],
                       result_full['lead_lname'],
                       "",
                       result_full['lead_address'],
                       json_data['lead_id'],
                       result_full['lead_age'],
                       result_full['lead_suffix'],
                       result_full['lead_city'],
                       result_full['lead_state'],
                       result_full['lead_zip'],
                       result_full['lead_zip4'],
                       result_full['lead_crrt'],
                       result_full['lead_dpbc'],
                       result_full['lead_fips'],
                       result_full['lead_est_debt']
                   )
   )

    ### Okay hopefully that worked lol
    connector.commit()

    ### Lets get the new data and return it
    SELECT_NEW_DATA = "SELECT * FROM tb_lead WHERE lead_id = %s"
    cursor.execute(SELECT_NEW_DATA, (json_data['lead_id'],))
    result_raw = cursor.fetchall()
    result_full = get_format_from_raw_full(result_raw, cursor)[0]
    result_full = encode_datetime(result_full)

    if (len(result_raw) < 0):
        ### Does exist
        return return_error(500, "Lead was not correctly initialized, please contact a systems administrator immediately!", result_full)

    return return_success(200, result_full)

def get_all_init_leads(data):
    # This funcction is designed to get us all of the existing leads that are in the initialized state but have
    # yet to actually call in at all
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

    # Determining what type of privilege check to make
    access_call = "get_lead_init"

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
    mydb = init_mysql("db_lead")
    cursor = mydb.cursor()

    select_init_leads = "SELECT * FROM tb_init_lead"
    cursor.execute(select_init_leads)

    result_raw = cursor.fetchall()
    result_full = get_format_from_raw_full(result_raw, cursor)[0]
    result_full = encode_datetime(result_full)

    if (len(result_raw) < 0):
        ### Does exist
        return return_error(500,
                            "Lead was not correctly initialized, please contact a systems administrator immediately!",
                            result_full)

    return return_success(200, result_full)


def init_leads_from_file(data):
    print("Attempting to initialize leads from a file")