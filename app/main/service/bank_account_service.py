import datetime

from app.main import db
from app.main.model.bank_account import BankAccount
from app.main.service.third_party.datax_service import validate_bank_account


def create_bank_account(client, data, override=False, overridable_codes=None):
    result, error = validate_bank_account(data.get('account_number'), data.get('routing_number'))
    if error:
        return None, error
    else:
        if result.get('valid') or (override and result.get('validation_code') in overridable_codes):
            new_bank_account = BankAccount(
                name=result.get('bank_name'),
                account_number=result.get('account_number'),
                routing_number=result.get('aba_number'),  # TODO: find out when/if I use 'NewRoutingNumber' or 'BankABA'
                valid=result.get('valid'),
                inserted_on=datetime.datetime.utcnow(),
                client=client
            )

            save_changes(new_bank_account)
            return new_bank_account, None
        else:
            validation_code = result.get('validation_code')
            if override:
                return None, dict(message='Error requires manager/admin for override', error_code=validation_code)
            return None, dict(message=result.get('validation_detail'), error_code=validation_code)


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()
