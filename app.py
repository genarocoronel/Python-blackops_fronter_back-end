# Importing libraries for use
# Importing flask
from bottle import Bottle, request
# Importing requests
# Importing JSON
from auth.validate import *
import sys
#sys.stdout = open('app_log.txt', 'w')

###########
## Tools ##
###########
from tools.employee import *
from tools.leads import *

#####################
## Phone Importing ##
#####################
from phone.load_dir import phone_load

############
## Notify ##
############
from notify.load_dir import notify_load

######################
## Authents Imports ##
######################
from auth.auth import authenticate

##################
## Call Imports ##
##################
from call.load_dir import call_load

######################
## Employee Imports ##
######################
from employee.load_dir import employee_load

##################
## Lead Imports ##
##################
from lead.load_dir import lead_load

#################
## SMS Imports ##
#################
from sms.load_dir import sms_load

#########################
## Appointment Imports ##
#########################
from appointment.load_dir import appointment_load

##########
## VOIP ##
##########
from voip.load_dir import voip_load

##################
## Chat Imports ##
##################
from chat.load_dir import chat_load
from mail.load_dir import mail_load

# Importing all of our helper python scripts
app = Bottle()

## This app file is where all of the routing is controlled. From here we are able to direct and manage all traffic
## accordingly. Note, that there is no actual functionality here, that is all done in the associated files

##################
## Core Routing ##
##################
## Core routing is some basic functionality.

@app.route('/')
def authenticate_default():
    print("Performing default authentication")
    auth_pass = authenticate(request.body.read(), "default", request.method)

    if (auth_pass):
        pass

@app.route('/status', method='GET')
def init():
    # Authenticating
    authenticate_default()

    return return_success(200, "Online")

######################
## Employee Routing ##
######################
## Employee routing for the basic functionality associated with employees.
employee_load(app)

#########################
## Appointment Routing ##
#########################
appointment_load(app)

##################
## Call Routing ##
##################
call_load(app)

#################
## SMS Routing ##
#################
sms_load(app)

##################
## Chat Routing ##
##################
chat_load(app)

##################
## Mail Routing ##
##################
mail_load(app)

###################
## Leads Routing ##
###################
lead_load(app)

####################
## Notify Routing ##
####################
notify_load(app)

##################
## Voip Routing ##
##################
voip_load(app)

app.run(host='0.0.0.0', port=5000)