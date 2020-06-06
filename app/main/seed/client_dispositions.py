import datetime
import uuid

from pytz import utc

from app.main import db
from app.main.model.client import ClientDisposition

client_dispositions = [
    {"value": 'Inserted',"select_type": 'AUTO', "name":'Sales_ActiveStatus_InsertedLead'},
    {"value": 'Transfer',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_Transfer'},
    {"value": 'Transfer is selected',"select_type": 'MANUAL', "name":'Sales_ActiveStaffmembers'},
    {"value": 'Attempted Contact',"select_type": 'AUTO', "name":'Sales_ActiveStatus_AttemptedContact'},
    {"value": 'Appointment Set',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_AppointmentSet'},
    {"value": 'Partial Options Pitch',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_PartialOptionPitch'}, 
    {"value": 'Pitched Options',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_PitchedOptions' },
    {"value": 'Pitched Credit Counseling',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_PitchedCreditCounseling'}, 
    {"value": 'Pitched Debt Validation',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_PitchedDebtValidation'},
    {"value": 'Pitched Bankruptcy',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_PitchedBankruptcy'},
    {"value": 'Enrolled in Credit Counseling',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_EnrolledCreditCounseling'}, 
    {"value": 'Enrolled in Bankruptcy',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_EnrolledBankruptcy'},
    {"value": 'Transferred to Credit Counseling',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_TransferredCreditCounseling' },
    {"value": 'Transferred to Bankruptcy',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_TransferredBankruptcy' },
    {"value": 'Budget Complete Only',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_BudgetComplete' },
    {"value": 'Resend Contract',"select_type": 'MANUAL', "name":'Sales_Status_ResendContract' },
    {"value": 'Contract Received',"select_type": 'AUTO', "name":'Sales_Contract_Received'},
    {"value": 'Contract Opened',"select_type": 'AUTO', "name":'Sales_Contract_Opened'},
    {"value": 'Contract Viewed',"select_type": 'AUTO', "name":'Sales_Contract_Viewed'},
    {"value": 'Contract Signed',"select_type": 'AUTO', "name":'Sales_Contract_Signed'},
    {"value": 'Contract Complete',"select_type": 'AUTO', "name":'Sales_Contract_Complete'},
    {"value": 'Contract Declined',"select_type": 'AUTO', "name":'Sales_Contract_Declined'},
    {"value": 'Contract Voided',"select_type": 'AUTO', "name":'Sales_Contract_Voided'},
    {"value": 'Contract Timed out',"select_type": 'AUTO', "name":'Sales_Contract_timedout'},
    {"value": 'Assign to Account Manager',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_AssignAcctManager' },
    {"value": 'Assign to Account Manager is selected',"select_type": 'MANUAL', "name":'Sales_ActiveStatus_AssignAcctManger_Selected' },
    {"value": 'Acct Manager Intro Complete',"select_type": 'AUTO', "name":'Service_ActiveStatus_AcctManagerIntroComplete' },
    {"value": 'Acct Manager Intro Incomplete',"select_type": 'MANUAL', "name":'Service_ActiveStatus_AcctManagerIntroIncomplete' },
    {"value": 'Deal Complete',"select_type": 'MANUAL', "name":'Service_ActiveStatus_DealComplete' },
    {"value": 'Deal Rejected',"select_type": 'MANUAL', "name":'Service_ActiveStatus_DealRejected' },
    {"value": 'Request Cancellation',"select_type": 'MANUAL', "name":'Service_ActiveStatus_RequestCancellation' },
    {"value": 'NSF',"select_type": 'AUTO', "name":'Service_ActiveStatus_NSF'},
    {"value": 'Draft/Banking Change',"select_type": 'MANUAL', "name":'Service_ActiveStatus_DraftBankingChange' },
    {"value": 'Service Issue Resolved',"select_type": 'MANUAL', "name":'Service_ActiveStatus_ServiceIssuesResolved' },
    {"value": 'Cancelled ',"select_type": 'MANUAL', "name":'Service_ActiveStatus_Cancelled' },
    {"value": 'Dead',"select_type": 'MANUAL', "name":'Sales_DeadStatus_ListofOptions' },
    {"value": 'DEAD: No credit card debt',"select_type": 'MANUAL', "name":'Sales_DeadStatus_NoCreditCardDebt' },
    {"value": 'DEAD: Already BK',"select_type": 'MANUAL', "name":'Sales_DeadStatus_AlreadyBankrupt' },
    {"value": 'DEAD: Cannot Afford',"select_type": 'MANUAL', "name":'Sales_DeadStatus_CannotAfford' },
    {"value": 'DEAD: Take off list',"select_type": 'MANUAL', "name":'Sales_DeadStatus_TakeoffList' },
    {"value": 'DEAD: Working with another company',"select_type": 'MANUAL', "name":'Sales_DeadStatus_WorkingWithOtherCompany' },
    {"value": 'DEAD: Do not call',"select_type": 'MANUAL', "name":'Sales_DeadStatus_DoNotCall' },
    {"value": 'DEAD: Paying off debt on their own',"select_type": 'MANUAL', "name":'Sales_DeadStatus_PayingOffDebtOnTheirOwn' },
    {"value": 'DEAD: Debt does not qualify',"select_type": 'MANUAL', "name":'Sales_DeadStatus_DebtDoesNotQualify' },
    {"value": 'DEAD: Not enough debt',"select_type": 'MANUAL', "name":'Sales_DeadStatus_NotEnoughDebt' },
    {"value": 'DEAD: No contact-Not Pitched',"select_type": 'MANUAL', "name":'Sales_DeadStatus_NoContact_NotPitched' },
    {"value": 'DEAD: Pitched DV then no contact',"select_type": 'MANUAL', "name":'Sales_DeadStatus_PitchedDV_ThenNoContact' },
    {"value": 'DEAD: Partial Pitch then no contact',"select_type": 'MANUAL', "name":'Sales_DeadStatus_PartialPitch_ThenNoContact' },
    {"value": 'DEAD: Heater',"select_type": 'MANUAL', "name":'Sales_DeadStatus_Heater'}
]


def seed_client_disposition_values():
    for disposition in client_dispositions:
        existing_disposition_value = ClientDisposition.query.filter_by(value=disposition['value']).first()
        if not existing_disposition_value:
            new_disposition = ClientDisposition(public_id=str(uuid.uuid4()), value=disposition['value'], select_type=disposition['select_type'], name=disposition['name'], inserted_on=datetime.datetime.now(tz=utc))
            db.session.add(new_disposition)
    db.session.commit()
