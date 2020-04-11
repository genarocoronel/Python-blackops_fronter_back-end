from app.main.model.team import TeamRequestType
from app.main import db

def seed_team_request_types():
    records = [
        {'code': 'REMOVE_DEBTS', 'title': 'Remove Debts', 'doc_sign': True,'description': 'Request to Remove Debts from existing contract'},
        {'code': 'ADD_DEBTS', 'title': 'Add Debts', 'doc_sign': True, 'description': 'Request to add debts to existing contract'},
        {'code': 'MODIFY_DEBTS','title': 'Modify Debts', 'doc_sign': True, 'description': 'Request to modify debts in existing contract'},
        {'code': 'RECIEVE_SUMMON', 'title': 'Receive Summon', 'doc_sign': True, 'description': 'Receive Summon of the existing debts'},
        {'code': 'TERM_CHANGE', 'title': 'Term Change', 'doc_sign': True, 'description': 'Change in number of monthly terms'},
        {'code': 'NEW_EFT_AUTH', 'title': 'New EFT Auth', 'doc_sign': True, 'description': 'New EFT Authorization'},
        {'code': 'ADD_COCLIENT', 'title': 'Add CoClient', 'doc_sign': True, 'description': 'Add co client to the contract.'},
        {'code': 'REMOVE_COCLIENT', 'title': 'Remove CoClient', 'doc_sign': True, 'description': 'Remove coclient from the contract'},
        {'code': 'CHANGE_DRAFT_DATE', 'title': 'Change Draft Date', 'doc_sign': False, 'description': 'Change next payment draft date'},
        {'code': 'SKIP_PAYMENT', 'title': 'Skip Payment', 'doc_sign': False,'description': 'Skip payment for the current cycle'},
        {'code': 'CHANGE_RECUR_DAY', 'title': 'Change Draft Day', 'doc_sign': False,'description': 'Change recurring payment day of the month'},
        {'code': 'RE_INSTATE', 'title': 'Reinstate', 'doc_sign': False, 'description': 'Reinstate an old client'},
        {'code': 'REFUND', 'title': 'Refund', 'doc_sign': False, 'description': 'Process Refund'},
    ]

    for record in records:
        req_type = TeamRequestType.query.filter_by(title=record['title']).first()
        if req_type is None:
            req_type = TeamRequestType(code=record['code'],
                                       title=record['title'],
                                       description=record['description']) 
            db.session.add(req_type)
        else:
            req_type.code = record['code']
            req_type.doc_sign_required = record['doc_sign']
           
    db.session.commit()

