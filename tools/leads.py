# Basic imports
import json
from bottle import Bottle, request
from pathlib import Path
import csv

# Config
from config.mysql_init import init_mysql
from auth.validate import return_error
from config.config import get_format_from_raw, get_format_from_raw_full
from config.glbl import get_global_path

#### Defining some global parameters
required_fields = ['FNAME', 'MI', 'LNAME', 'SUFFIX', 'ADDRESS', 'CITY', 'STATE', 'ZIP', 'ZIP4', 'CRRT', 'DPBC', 'FIPS', 'EST DEBT ', 'AGE', 'COUNTY']

### Helper function for checking if input params exist
def check_required_fields(row, fields):

    for field in fields:
        if field not in row:
            print("Missing " + field + " in " + str(row))
            return False

    return True

### Main file for dealing with lead input from file...
def init_leads_from_file(file, options):
    # Options will contain all of the generation information...

    print("Initializing all of the leads from the file")
    print("First we are checking if we already initialized this file")
    print("This is important so we don't send mail TWICE...")

    db = init_mysql("db_log")
    cursor = db.cursor()

    # Checking...
    check_file = "SELECT * FROM tb_lead_load_log WHERE file_name = %s"
    cursor.execute(check_file, (file,))

    results_raw = cursor.fetchall()
    result = get_format_from_raw_full(results_raw, cursor)

    if len(results_raw) > 0:
        # Error!
        return return_error(500, "File already loaded and did not recieve override, exiting", "")

    ### Okay, file has not been loaded
    ### Lets check if the file even exists first... :D
    path = get_global_path() + "/mail/mail_files/" + file
    print("Checking if file exists (path: " + path + ")")

    try:
        file = Path(path)
        if not file.is_file():
            print("Error, file does not exist")
            return return_error(500, "File does not exist!")
    except:
        print("Error!")

    print("File does exist, loading...")

    with open(path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:

            if line_count == 0:

                # Lets check if the first row matches what we expect
                # We are supposed to have a variety of important information here...
                if not check_required_fields(row, required_fields):
                    print("Invalid CSV file, missing parameter")
                    return return_error(500, "Invalid input file, missing one of the required fields from the following list", required_fields)

                line_count += 1
            else:
                # If we made it this far, we have actually recieved valid input...
                # Its time to load this individual into our database...
                insert_statement = "INSERT INTO db_lead.tb_init_lead (lead_fname, lead_mi, lead_lname, lead_suffix, lead_address, lead_city, lead_state, lead_zip, lead_zip4, lead_crrt, lead_dpbc, lead_fips, lead_est_debt, lead_age, lead_county) VALUES" \
                                   "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

                # Loading values
                value = []
                for entry in row:
                    value.append(entry)

                cursor.execute(insert_statement,value)

    # Commiting changes
    db.commit()

    # Indicating we have opened this file in our internal system

### Mail function for converting a lead set into a functional mail set
### Given a set of options, will generate a mail set file to be sent to redstone
def build_redstone_file(options):
    print("Generating redstone file")
