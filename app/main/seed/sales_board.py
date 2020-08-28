from app.main.model.sales_board import SalesBoard, LeadDistributionProfile, DistributionHuntType
from app.main.model.user import User, Department
from app.main.model import Language
from app.main import db

def seed_lead_distro_profile():
    records = [
        {'hunt_type': DistributionHuntType.PRIORITY.name, 'flow_interval': 10, 'language': Language.ENGLISH.name},
        {'hunt_type': DistributionHuntType.PRIORITY.name, 'flow_interval': 10, 'language': Language.SPANISH.name},
    ]

    for record in records:
        profile = LeadDistributionProfile.query.filter_by(language=record['language']).first()
        if not profile:
            profile = LeadDistributionProfile(hunt_type=record['hunt_type'],
                                              flow_interval=record['flow_interval'],
                                              language=record['language'])
            db.session.add(profile)

    db.session.commit()


def create_sales_boards():

    for user in User.query.all():
        dept = Department.from_role(user.role.name)
        if dept == Department.SALES.name:
            sales_board = SalesBoard.query.filter_by(agent_id=user.id).first()
            if not sales_board:
                sales_board = SalesBoard(agent_id=user.id)
                db.session.add(sales_board)
    db.session.commit()
