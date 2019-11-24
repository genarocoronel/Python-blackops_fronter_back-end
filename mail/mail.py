# Basic imports
import json
from bottle import Bottle, request
import smtpd
import smtplib
from smtplib import SMTPException
import asyncore
import email
from email.header import decode_header
from auth.validate import return_success
import threading

# Input checker
from auth.validate import check_inputs_exist, return_error, sanitize, generate_hash, return_success, random_digit
from auth.auth import check_your_privilege, auth_token

# Employee logging
from employee.employee import employee_log

# Config
from config.mysql_init import init_mysql
from config.config import get_format_from_raw, get_format_from_raw_full

### This is the mail class
server = None
server_status = "Offline"
loop_thread = None


### Sigh, will probably have to add race condition handling stuff here at some point...
### TODO: Handle race conditions

def stop_mail():
    global loop_thread, server, server_status
    server.quit()
    server = None
    server_status = "Offline"
    loop_thread = None

def start_mail():
    global server, server_status
    server = smtpd.SMTPServer(('0.0.0.0', 25), None)
    server_status = "Online"

    global loop_thread
    loop_thread = threading.Thread(target=asyncore.loop, name="Asyncore Loop")
    # If you want to make the thread a daemon
    # loop_thread.daemon = True
    loop_thread.start()

class CustomSMTPServer(smtpd.SMTPServer):

    def debug(self):
        print("Hello World!")

    def process_message(self, peer, mailfrom, rcpttos, data):

        print("Processing inbound email")
        message = email.message_from_string(data)
        attachments = []

        subject = ''
        for encoded_string, charset in decode_header(message.get('Subject')):
            try:
                if charset is not None:
                    subject += encoded_string.decode(charset)
                else:
                    subject += encoded_string
            except:
                print("ERROR PROCESSING SUBJECT MESSAGE, RETURNING")
                return

        for part in message.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            c_type = part.get_content_type()
            c_disp = part.get('Content-Disposition')

            # text parts will be appended to text_parts
            if c_type == 'text/plain' and c_disp == None:
                #print("Recieved text parts")
                continue
            # ignore html part
            elif c_type == 'text/html':
                #print("Ignoring html")
                continue

            # attachments will be sent as files in the POST request
            else:
                filename = part.get_filename()
                filecontent = part.get_payload(decode=True)
                if filecontent is not None:
                    if filename is None:
                        filename = 'untitled'
                    with open("./mail/mail_files/"+str(filename), 'wb') as file:
                        file.write(filecontent)

                attachments.append(filename)
        # Making sure to insert this info into our database...
        connector = init_mysql("db_mail")

        ## TODO: VALIDATE AND SANITIZE THE EMAIL INPUTS BECAUSE JESUS THINGS COULD GO WRONG HERE

        # Saving this as recieved
        sender = mailfrom
        attachments_str = str(attachments)

        cursor = connector.cursor()
        insert = "INSERT INTO tb_mail_recieved (mail_sender, mail_attachments, mail_body, mail_subject) VALUES (%s, %s, %s, %s)"

        cursor.execute(insert, (sender, attachments_str, "", subject))
        connector.commit()

        return


def mail_server_start(data):
    print("Starting mail server")

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
    sanitize_list = ["integer", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "email_server_status_edit"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get email server status")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get email server status")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    ### If server is already online, lets not do anything
    global server_status
    if (server_status == "Online"):
        return return_error(500, "Mail Server already Online", "")

    print("Starting internal mail server")
    start_mail()


def mail_server_stop(data):
    print("Stopping mail server")

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
    sanitize_list = ["integer", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "email_server_status_edit"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get email server status")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get email server status")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    print("Stopping internal mail server")
    stop_mail()

def mail_server_status(data):
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
    sanitize_list = ["integer", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "email_server_status_get"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get email server status")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get email server status")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    global server, server_status
    return return_success(200, {"status_text": "Mail Server Status: " + str(server_status), "status": server_status})

def send_mail(data):
    # Function for sending an email

    # Grabbing our data
    if len(data) <= 0:
        return return_error(500, "Missing input set", "")

    # Grabbing our data
    # TODO: Add input sanitization on the json load
    json_data = json.loads(data)

    # Checking for required data entries
    req_entry = ["employee_id", "employee_auth", "address", "body", "subject"]
    if (not check_inputs_exist(req_entry, json_data)):
        return return_error(500, "Missing input set", "")

    # Sanitizing
    sanitize_list = ["integer", "string"]
    json_data = sanitize(json_data, req_entry, sanitize_list)

    # Determining what type of privilege check to make
    access_call = "email_send"

    # Checking for required data entries
    ### Performing auth check ###
    if not auth_token(json_data['employee_id'], json_data['employee_auth']):
        employee_log(json_data['employee_id'],
                     "Failed auth check to get email server status")
        return return_error(490, "Invalid authentication token", "")

    ### Performing Permissions Check ###
    if not check_your_privilege(json_data['employee_id'], access_call):
        employee_log(json_data['employee_id'],
                     "Failed privilege check to get email server status")
        return return_error(490, "Invalid privilege", "")

    ### BOILER PLATE END ###

    ### TODO: Add employee logging to ALL REQUESTS EVEN ON SUCCESS
    ### TODO: REMEMBER TO DO THIS SOMETIME SOONISH!!!

    ### Checking if the mail server is running first...
    if server_status == "Offline":
        return return_error(500, "Mail server is offline","")

    smtp_connection = smtplib.SMTP('localhost',25)
    smtp_connection.sendmail('test@test.com','alexander@lajolladev.com',"Hello World!")
    smtp_connection.quit()
