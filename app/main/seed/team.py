from app.main.model.team import TeamRequestType
from app.main import db

def seed_team_request_types():
    records = [
        {'title': 'Remove Debts', 'description': 'Request to Remove Debts from existing contract'},
        {'title': 'Add Debts', 'description': 'Request to add debts to existing contract'},
        {'title': 'Modify Debts', 'description': 'Request to modify debts in existing contract'},
    ]

    for record in records:
        req_type = TeamRequestType.query.filter_by(title=record['title']).first()
        if req_type is None:
            req_type = TeamRequestType(title=record['title'],
                                       description=record['description']) 
            db.session.add(req_type)

    db.session.commit()

