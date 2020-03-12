from app.main.model.bank_account import BankAccountValidationStatus, StatusCategory
from app.main import db


def seed_datax_validation_codes():
    #passed codes
    if not BankAccountValidationStatus.query.filter_by(code='1111').first():
        bav01 = BankAccountValidationStatus(code='1111', category=StatusCategory.passed, title='Pass AV', description='Account Verified: The account was found to be an open and valid account.')
        db.session.add(bav01)
    if not BankAccountValidationStatus.query.filter_by(code='XD00').first():
        bav02 = BankAccountValidationStatus(code='XD00', category=StatusCategory.passed, title='No Data', description='No positive or negative information has been reported on the account. This could be a small or regional bank that does not report.')
        db.session.add(bav02)
    if not BankAccountValidationStatus.query.filter_by(code='XD01').first():
        bav03 = BankAccountValidationStatus(code='XD01', category=StatusCategory.passed, title='No Data-US Government Only', description='No positive or negative information has been reported on the account. This routing number can only be valid for US Gov. financial institution.')
        db.session.add(bav03)
    if not BankAccountValidationStatus.query.filter_by(code='3333').first():
        bav04 = BankAccountValidationStatus(code='3333', category=StatusCategory.passed, title='Pass NPP', description='Non-Participant Provider- This item was reported with acceptable, positive data found recent or current transactions.')
        db.session.add(bav04)
    if not BankAccountValidationStatus.query.filter_by(code='P01').first():
        bav05 = BankAccountValidationStatus(code='P01', category=StatusCategory.passed, title='Pass LR', description='Account associated with a low risk ABA, no recent fatal returns, and low return rate')
        db.session.add(bav05)
    if not BankAccountValidationStatus.query.filter_by(code='P02').first():
        bav06 = BankAccountValidationStatus(code='P02', category=StatusCategory.passed, title='No Recent Returns', description='Account has at least 1 successful payment in the past 30 days and no returns within 30 days')
        db.session.add(bav06)
    if not BankAccountValidationStatus.query.filter_by(code='P03').first():
        bav07 = BankAccountValidationStatus(code='P03', category=StatusCategory.passed, title='Aged Account', description='Account is more than 6 months old with a no returned payments within past 30 days')
        db.session.add(bav07)
    if not BankAccountValidationStatus.query.filter_by(code='P04').first():
        bav08 = BankAccountValidationStatus(code='P04', category=StatusCategory.passed, title='Active Account', description='Account is at least 545 days old and currently being used')
        db.session.add(bav08)
    if not BankAccountValidationStatus.query.filter_by(code='P05').first():
        bav09 = BankAccountValidationStatus(code='P05', category=StatusCategory.passed, title='No Returns Past 6 Months', description='Account has no return payments in the past 180 days')
        db.session.add(bav09)

    # failure codes
    if not BankAccountValidationStatus.query.filter_by(code='XB01').first():
        bav10 = BankAccountValidationStatus(code='XB01', title='Invalid Routing Number', description='The status of the Routing Number was found to be invalid.')
        db.session.add(bav10)
    if not BankAccountValidationStatus.query.filter_by(code='XS04').first():
        bav11 = BankAccountValidationStatus(code='XS04', title='Invalid Amount', description='The amount supplied did not match the format of a valid amount.')
        db.session.add(bav11)
    if not BankAccountValidationStatus.query.filter_by(code='XT00').first():
        bav12 = BankAccountValidationStatus(code='XT00', title='No Information Found', description='The routing number appears to be accurate however, no positive or negative information has been reported on the account. ')
        db.session.add(bav12)
    if not BankAccountValidationStatus.query.filter_by(code='XT01').first():
        bav13 = BankAccountValidationStatus(code='XT01', title='Declined', description='This account should be returned based on the risk factor being reported.')
        db.session.add(bav13)
    if not BankAccountValidationStatus.query.filter_by(code='XT02').first():
        bav14 = BankAccountValidationStatus(code='XT02', title='Stop Payment', description='A stop payment has been issued for this individual check or this is a check within a range of checks that have been issued a stop payment.')
        db.session.add(bav14)
    if not BankAccountValidationStatus.query.filter_by(code='XT03').first():
        bav15 = BankAccountValidationStatus(code='XT03', title='Accept with Risk', description='Current negative data exists on the account. Accept transaction with risk. (Example: Checking/Savings account in NSF status, recent returns, or outstanding items)')
        db.session.add(bav15)
    if not BankAccountValidationStatus.query.filter_by(code='XT04').first():
        bav16 = BankAccountValidationStatus(code='XT04', title='No Negative Data', description='The account is a Non Demand Deposit Account (posts no debits), credit card check, line of credit check, home equity, brokerage check, non-participant, non-DDA.')
        db.session.add(bav16)
    if not BankAccountValidationStatus.query.filter_by(code='XN01').first():
        bav17 = BankAccountValidationStatus(code='XN01', title='Negative Data', description='Negative information was found in this account history.')
        db.session.add(bav17)
    if not BankAccountValidationStatus.query.filter_by(code='XN05').first():
        bav18 = BankAccountValidationStatus(code='XN05', title='Decline', description='The routing number supplied is reported\
                                        as not assigned to a financial institution.')
        db.session.add(bav18)
    if not BankAccountValidationStatus.query.filter_by(code='N01').first():
        bav19 = BankAccountValidationStatus(code='N01', title='Decline 1', description='Account associated with a high risk ABA and payments have been fatally returned (return codes: R02, R05, R07, R08, R10, or R16)')
        db.session.add(bav19)
    if not BankAccountValidationStatus.query.filter_by(code='N02').first():
        bav20 = BankAccountValidationStatus(code='N02', title='Negative Data – Thin History', description='Account has a thin history with negative items and has limited activity')
        db.session.add(bav20)
    if not BankAccountValidationStatus.query.filter_by(code='N03').first():
        bav21 = BankAccountValidationStatus(code='N03', title='Fatal Return', description='Account has a fatal return (return codes: R02, R05, R07, R08, R10, or R16) payment history')
        db.session.add(bav21)
    if not BankAccountValidationStatus.query.filter_by(code='N04').first():
        bav22 = BankAccountValidationStatus(code='N04', title='Decline 2', description='Account associated with high risk ABA and last known payment has been returned.')
        db.session.add(bav22)

    db.session.commit()
