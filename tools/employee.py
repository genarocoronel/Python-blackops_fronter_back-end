### Employee tools
import datetime

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# SMS
from sms.sms import sms_send_raw

# Config
from config.mysql_init import init_mysql, build_edit_query
from config.config import get_format_from_raw_full, date_to_string, get_format_from_raw

### Employee tool for determining which employee to route a call too
def get_next_available_employee():
    ### Will allow us to determine the ID of the next employee to route to
    ### TODO: Implement round-robin style tracking of employee's

    connector = init_mysql('db_employee')
    cursor = connector.cursor()

    select_active = "SELECT * FROM tb_employee_status WHERE employee_status = %s"
    cursor.execute(select_active, ("active",))
    results = cursor.fetchall()

    ### Okay we have all of our active employees...
    ### From this, lets check their current call status
    select_call_tracking = "SELECT * FROM tb_employee_call_tracking INNER JOIN db_call.tb_call WHERE db_call.tb_call.call_id = tb_employee_call_tracking.call_id AND ("

    ### Building employee list
    employee_list = []

    ### Appending...
    for result_employee in results:
        select_call_tracking = select_call_tracking + " employee_id = %s OR"
        employee_list.append(result_employee[0])

    ### Fixing
    select_call_tracking = select_call_tracking[0:len(select_call_tracking) - 3]
    select_call_tracking = select_call_tracking + ")"

    ### Executing...
    cursor.execute(select_call_tracking, employee_list)
    result_call_tracking = cursor.fetchall()
    result_full = get_format_from_raw_full(result_call_tracking, cursor)

    ### Lets check; did anyone just simply not have any call ever yet?
    employee_call_list = {}

    for result in result_full:
        employee_id = result['employee_id']
        employee_call_list[employee_id] = result

    print(employee_call_list)

    ### Checking if any of our employees THAT ARE ACTIVE have NOT recieved a call yet...
    for employee in employee_list:
        if employee not in employee_call_list:
            return employee

    ### Okay, so if we've made it this far all of our active employees have been initialized
    ### Now what we want to do is (hopefully) give the inbound call to the least recently given employee
    ### Do this by sorting by datetime on inactive calls (inactive calls ONLY)
    earliest_call = datetime.datetime.now()
    earlist_call_employee = -1

    for employee in employee_call_list:
        call = employee_call_list[employee]
        if call['call_status'] != 0:
            continue

        call = call['call_end']
        if call < earliest_call:
            earliest_call = call
            earlist_call_employee = employee

    ### Okay, lets see
    if not earlist_call_employee == -1:
        return earlist_call_employee

    ### TODO: Sort by inactive calls

    ### Okay, shit, we have all calls full!!!
    ### We need to through this guy into the 'please hold' queue...
    ### Thats bad lol


### Function for getting employee phone number from id
def get_phone_from_employee_id(id):
    print("Getting employee route number from their ID")

    mydb = init_mysql("db_employee")
    cursor = mydb.cursor()

    select = "SELECT employee_phone_route FROM db_employee.tb_employee WHERE employee_id = %s"
    cursor.execute(select, (id,))
    result_raw = cursor.fetchall()
    result = get_format_from_raw(result_raw, cursor)

    return result['employee_phone_route']

