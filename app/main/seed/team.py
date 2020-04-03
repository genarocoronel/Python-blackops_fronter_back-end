from app.main.model.team import TeamRequestType
from app.main import db

def seed_team_request_types():
    records = [
        {'title': 'Remove Debts', 'description': 'Request to Remove Debts from existing contract'},
        {'title': 'Add Debts', 'description': 'Request to add debts to existing contract'},
        {'title': 'Modify Debts', 'description': 'Request to modify debts in existing contract'},
        {'title': 'Receive Summon', 'description': 'Receive Summon of the existing debts'},
        {'title': 'Term Change', 'description': 'Change in number of monthly terms'},
        {'title': 'New EFT Auth', 'description': 'New EFT Authorization'},
        {'title': 'Add CoClient', 'description': 'Add co client to the contract.'},
        {'title': 'Remove CoClient', 'description': 'Remove coclient from the contract'},
    ]

    for record in records:
        req_type = TeamRequestType.query.filter_by(title=record['title']).first()
        if req_type is None:
            req_type = TeamRequestType(title=record['title'],
                                       description=record['description']) 
            db.session.add(req_type)

    db.session.commit()

