from twilio.rest import Client

from app.main import db
from app.main.model.sms import SMSMessage

account_sid = "AC27a28affdf746d9c7b06788016b35c8c"
sms_auth_token = "a91db8822f78e7a928676140995290db"


def sms_send_raw(phone_target, sms_text, user_id):
    print("Sending an SMS to " + phone_target)

    client = Client(account_sid, sms_auth_token)

    new_sms_message = SMSMessage(user_id=user_id, text=sms_text, phone_target=phone_target, status='created')

    try:
        message = client.messages.create(
            to=phone_target,
            from_="+18584139754",
            body=sms_text)
        new_sms_message.message_provider_id = message.sid
        new_sms_message.status = 'sent'
    except Exception as e:
        new_sms_message.status = 'failed_to_send'
    finally:
        db.session.add(new_sms_message)
        db.session.commit()
