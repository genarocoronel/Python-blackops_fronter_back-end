from app.main.model.checklist import CheckList
from app.main import db


def seed_client_main_checklist():
    values = ['Brand Phone Number', 
              'Summon', 
              'Collection Violation',
              'Not Debt Settlement',
              'Financial Rehabilitation',
              'Smart Credit',
              'Smart Credit: Co-Client',
              'FDCPA Attorney Intro',
              'Fully Disputed',   
              'Salesman Declaration-March 21, 2019 by Sarah Flores', ]

    for value in values:
        cl = CheckList.query.filter_by(title=value).first() 
        if cl is None:
            cl = CheckList(title=value)
            db.session.add(cl)

    db.session.commit()

