from app.main.model.sales_board import LeadDistributionProfile, DistributionHuntType
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
