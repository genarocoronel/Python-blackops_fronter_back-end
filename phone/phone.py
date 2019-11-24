# Basic imports
import json
from bottle import Bottle, request

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Config
from config.mysql_init import init_mysql


# Function for routing of inbound phone calls
def phone_route_inbound(data):
    print ("Recieved an inbound request!")

    return return_success(200,"18586686091")