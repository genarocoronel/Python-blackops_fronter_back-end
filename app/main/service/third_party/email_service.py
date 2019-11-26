import imaplib
import base64
import os
import email
from imaplib import IMAP4_SSL


def connect(username: str, password, host: str, port: int):
    mail = imaplib.IMAP4_SSL(host, port)
    mail.login(username, password)

    return mail


def get_mail_from_label(mail: IMAP4_SSL, label: str, filter: str):
    mail.select(label)
    type, data = mail.search(None, 'ALL')
    mail_ids = data[0]
    id_list = mail_ids.slit()

    first_email_id = int(id_list[0])
    last_email_id = int(id_list[-1])

