import string
import random
import hashlib
import json

#######################
## Private Functions ##
#######################

# Function for returning errors, where appropriate
def return_error(code, reason, data):
    return_result = {'code': code, 'reason': reason, 'output': data}
    return_result = json.dumps(return_result)
    return return_result

def return_success(code, data):
    return_result = {'code': code, 'output': data}
    return_result = json.dumps(return_result)
    return return_result

# Authenticating against a set of inputs, checking if they exist
# Fails and returns false if they dont exist
# Needs a string list and a JSON data object
def check_inputs_exist(list, json_data):
    print("Checking for existing set of keys")
    print(list)
    print(json_data)

    if len(list) <= 0:
        return False

    for key in list:
        if key not in json_data:
            return False

    return True

# Function for input sanitzation
def sanitize(json_data, req_entry, json_sanitize_list):
    # print("Sanitizing inputs")

    # TODO: Add sanitization here...

    return json_data

# Function for generating hashes
def generate_hash():
    value = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(128))
    hash = hashlib.sha512(value.encode())
    return hash

# Function for generating a random digit
def random_digit(size):
    output = ""

    for x in range(0,size):
        random_number = random.randrange(0,9)
        output = output + str(random_number)

    return output