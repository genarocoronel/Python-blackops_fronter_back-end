import datetime

from app.main import db
from app.main.model.bank_account import BankAccount
from app.main.service.third_party.datax_service import validate_bank_account
from app.main.model.bank_account import BankAccountValidationStatus, BankAccountValidationHistory
from app.main.util.decorator import enforce_rac_required_roles
from app.main.core.rac import RACRoles
from flask import g


@enforce_rac_required_roles([RACRoles.SERVICE_MGR, RACRoles.SERVICE_REP])
def create_bank_account(client, data):
    req_user = g.current_user 
    # user id
    user_id = req_user['user_id']
    # user role
    user_role = req_user['rac_role']
    override = data.get('override')
    # override is allowed only for service managers
    if override and (user_role != RACRoles.SERVICE_MGR.value and 
                     user_role != RACRoles.ADMIN.value):
        override = False
    
    account_number = data.get('account_number')
    routing_number = data.get('routing_number')

    result, error = validate_bank_account(account_number, routing_number)
    if error:
        return None, error
    else:
        code = result.get('code')
        message = "Account validation passed" if result.get('valid') else "Account validation failed"
        if code is not None:
            bav_status = BankAccountValidationStatus.query.filter_by(code=code).first()
            if bav_status is not None:
                message = bav_status.description

        is_valid = result.get('valid')
        overrule_status = False
        overruled_by = None
        # account validation failed
        # check override fla is ser or not
        if not is_valid and override:
            overrule_status = True
            overruled_by = user_id

        # create validation History
        bav_history = BankAccountValidationHistory(client_id=client.id,
                                                  account_number=account_number,
                                                  routing_number=routing_number,
                                                  overuled=overrule_status,
                                                  overuled_by=overruled_by,                               
                                                  timestamp=datetime.datetime.utcnow())               
        if bav_status is not None:
            bav_history.bav_status_id = bav_status.id
        save_changes(bav_history) 

        if result.get('valid') or override:
            acct_owner = data.get('owner_name')
            acct_address = data.get('address')
            acct_city = data.get('city')
            acct_state = data.get('state')
            acct_zip = data.get('zip')
            acct_ssn = data.get('ssn')
            acct_email = data.get('email')

            bank_name = result.get('bank_name')
            if bank_name is None:
                bank_name = data.get('bank_name')
            # check bank account exists	
            bank_account = client.bank_account
            if bank_account is None:
                new_bank_account = BankAccount(
                    bank_name=bank_name,
                    account_number=result.get('account_number'),
                    routing_number=result.get('aba_number'),  # TODO: find out when/if I use 'NewRoutingNumber' or 'BankABA'
                    valid=result.get('valid'),
                    inserted_on=datetime.datetime.utcnow(),
                    client_id=client.id,
                    owner_name = acct_owner,
                    email = acct_email,
                    address = acct_address, 
                    city = acct_city,
                    state = acct_state,
                    zip = acct_zip,
                    ssn = acct_ssn, 
                )
                if bav_status is not None:
                    new_bank_account.bav_status_id = bav_status.id
                
                save_changes(new_bank_account)
            else:
                bank_account.bank_name = bank_name
                bank_account.account_number = result.get('account_number')
                bank_account.routing_number = result.get('aba_number')
                bank_account.valid = True
                bank_account.owner_name = acct_owner
                bank_account.email = acct_email

                db.session.commit()
            
            data['bank_name'] = bank_name
            data['account_number'] = result.get('account_number')
            data['routing_number'] = result.get('aba_number')
            result = {
                'aba_valid': True,
                'acct_valid': True,
                'valid': True,
                'override': overrule_status,
                'code': code,
                'message': message,
                'bank_account': data,
            }
            return result, None
        else:

            result = {
                'aba_valid': result.get('aba_valid'),
                'acct_valid': result.get('acct_valid'),
                'valid': False,
                'code': code,
                'message': message,
                'bank_account': {},
            }
            return result, None


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()
