import datetime

#######################
## Private Functions ##
#######################

def get_format_from_raw(raw, cursor):
   result = [dict(line) for line in [zip([column[0] for column in cursor.description], row) for row in raw]][0]
   return result

def get_format_from_raw_full(raw, cursor):
   result = [dict(line) for line in [zip([column[0] for column in cursor.description], row) for row in raw]]
   return result

def date_to_string(datetime):
    output = datetime.strftime("%Y-%m-%d %H:%M:%S")
    return output

### Converting all instances of datetime into a string for output purposes
### Requires an array as input
def encode_datetime(result):

    # Performing format fix
    new_result_output = []
    for value in result:

        ### Building the new output value
        new_value = value

        for element in value:

            if element not in value:
                continue

            if not isinstance(value, dict):
                continue

            data = value[element]
            if isinstance(data, datetime.datetime):

                new_value[element] = date_to_string(value[element])

        new_result_output.append(new_value)

    return new_result_output


