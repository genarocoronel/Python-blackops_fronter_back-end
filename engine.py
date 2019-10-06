# The engine is a tool that will run in the background
import time
import sys
import datetime

# Importing tools
from config.mysql_init import *
from config.config import *

### Some engine configs go right here
MAX_INACTIVE_TIME_SECONDS = 180

###

def init():
    print("Engine is starting up...")
    print("Insert cool noises")

    while(True):

        update_employee_activity()
        time.sleep(1)

### Function that will turn employees inactive based off of activity log tracking
def update_employee_activity():

    connector = init_mysql("db_employee")
    cursor = connector.cursor()

    select = "SELECT * FROM tb_employee_status INNER JOIN tb_employee_activity_log WHERE tb_employee_status.employee_id = tb_employee_activity_log.employee_id"
    cursor.execute(select)
    result_raw = cursor.fetchall()
    result = get_format_from_raw_full(result_raw, cursor)

    ### Checking status
    for entry in result:
        ### Getting variables
        employee_id = entry['employee_id']
        last_update = entry['last_update']
        status = entry['employee_status']

        # Ignoring status updates for inactive; we only want to update active people
        # We CAN turn this off if we want; but it will make this take longer (but ensure activity is properly set)
        if status == "inactive":
            continue

        # Checking datetime differences
        now = datetime.datetime.now()
        delta = now - last_update
        delta_seconds = delta.seconds

        if (delta_seconds) > MAX_INACTIVE_TIME_SECONDS:
            ### Setting this employee to inactive...
            set_inactive = "UPDATE tb_employee_status SET employee_status = 'inactive' WHERE employee_id = %s"
            cursor.execute(set_inactive, (employee_id,))

    connector.commit()





print("Initializing the engine...")
init()