from typing import List

from flask import current_app as app

from app.main.service.email_service import send_mail


def send_fax(phone_number: int, subject: str, attachments: List[str]) -> str:
    FAX_SENDER = app.fax_sender  # example: elitedoc@thedeathstarco.com
    FAX_SERVICE_DOMAIN = app.fax_service_domain  # example: elitedoc.fax.onjive.com
    FAX_ACCESS_CODE = app.fax_access_code  # example: 4662176

    recipient = f'{phone_number}@{FAX_SERVICE_DOMAIN}'
    result = send_mail(FAX_SENDER, [recipient], f'{FAX_ACCESS_CODE} {subject}', None, None, attachments)
    return result.get('MessageId')
