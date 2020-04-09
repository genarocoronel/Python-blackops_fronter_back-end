from phonenumbers import PhoneNumber

from app.main.service.candidate_service import get_candidate_contact_by_phone
from app.main.service.client_service import get_client_contact_by_phone


def identify_customer_by_phone(phone: PhoneNumber):
    customer_contact = get_client_contact_by_phone(phone)
    if customer_contact is None:
        customer_contact = get_candidate_contact_by_phone(phone)
        customer = customer_contact.candidate if customer_contact else None
    else:
        customer = customer_contact.client
    return customer
