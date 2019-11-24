### File for tools dealing with class
def get_inbound_call_number(data):
    phone_inbound_start = data.index("&Caller=%2B") + 11
    phone_inbound_end = data.index("&FromCountry=")
    inbound_phone = data[phone_inbound_start:phone_inbound_end]

    return inbound_phone

def get_call_sid(data):
    phone_call_sid_start = data.index("&CallSid=") + 9
    phone_call_sid_end = data.index("&", phone_call_sid_start)
    call_sid = data[phone_call_sid_start:phone_call_sid_end]
    print("CALL SID IS: " + call_sid)

    return call_sid