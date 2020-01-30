import datetime
import uuid

from pytz import utc

from app.main import db
from app.main.model.candidate import CandidateDisposition

candidate_dispositions = [
    {'value':'Hung up in less than 1 minute','select_type':'AUTO', 'name':'Opener_ActiveHungup'},
    {'value':'Missed Call','select_type':'AUTO', 'name':'Opener_ActiveMissedCall'},
    {'value':'New Lead','select_type':'AUTO', 'name':'Opener_ActiveNewLead'},
    {'value':'Missed Call-Attempting to contact','select_type':'AUTO', 'name':'Opener_ActiveMissedCallAttemptingContact'},
    {'value':'Working Lead','select_type':'MANUAL', 'name':'Opener_ActiveWorkingLead'},
    {'value':'Working Lead-SmartCredit Issue','select_type':'MANUAL', 'name':'Opener_ActiveWorkingLeadSCIssue'},
    {'value':'Submitted','select_type':'AUTO', 'name':'Opener_ActiveSubmittedApplicationCreatedDate'},
    {'value':'Dead: Will not give personal info','select_type':'MANUAL', 'name':'Opener_DeadWontGivePersonalInfo'},
    {'value':'Dead: Locked out of smart credit','select_type':'MANUAL', 'name':'Opener_DeadLockedOutSC'},
    {'value':'Dead: Unfamiliar with Brand','select_type':'MANUAL', 'name':'Opener_DeadUnfamiliarWithBrand'},
    {'value':'Dead: Going with another company','select_type':'MANUAL', 'name':'Opener_DeadGoingwithothercompany'},
    {'value':'Dead: Wrong Phone Number','select_type':'MANUAL', 'name':'Opener_DeadWrongPhoneNumber'},
    {'value':'Dead: Could not reach','select_type':'MANUAL', 'name':'Opener_DeadCouldNotreach'},
    {'value':'Dead: No longer interested','select_type':'MANUAL', 'name':'Opener_DeadNoLongerinterested'},
    {'value':'Dead: Take off list/Do not call','select_type':'MANUAL', 'name':'Opener_DeadDoNotCallTakeOffList'},
    {'value':'Dead: No Invitation ID number','select_type':'MANUAL', 'name':'Opener_DeadNoInvitationID'},
    {'value':'Dead: No debt','select_type':'MANUAL', 'name':'Opener_DeadNoDebt'},
    {'value':'Dead: Wrong address','select_type':'MANUAL', 'name':'Opener_DeadWrongAddress'},
    {'value':'Dead: Duplicate info','select_type':'MANUAL', 'name':'Opener_DeadDuplicateInfo'},
    {'value':'Dead: Dead','select_type':'MANUAL', 'name':'Opener_DeadNoSpecificReason'},
    {'value':'Dead: Stop Texting','select_type':'MANUAL', 'name':'Opener_DeadStopTexting'},
    {'value':'Dead: Old','select_type':'MANUAL', 'name':'Opener_DeadOld'},
    {'value':'Dead: Fax','select_type':'MANUAL', 'name':'Opener_DeadFax'},
    {'value':'Dead: Other','select_type':'MANUAL', 'name':'Opener_DeadOther'}
]


def seed_candidate_disposition_values():
    for disposition in candidate_dispositions:
        existing_disposition_value = CandidateDisposition.query.filter_by(value=disposition['value']).first()
        if not existing_disposition_value:
            new_disposition = CandidateDisposition(public_id=str(uuid.uuid4()), value=disposition['value'], select_type=disposition['select_type'], name=disposition['name'], inserted_on=datetime.datetime.now(tz=utc))
            db.session.add(new_disposition)
    db.session.commit()
