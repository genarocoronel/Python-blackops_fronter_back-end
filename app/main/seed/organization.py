from app.main.model.organization import *

def seed_organizations():
    records = [
        {'name': 'Elite DMS', 'url': 'https://elitemgtsol.com/', 'logo_url':'https://client.elitemgtsol.com/content/images/logoEmailTemplate.jpg', 'client_portal': 'https://client.elitemgtsol.com/', 'app_name':'Elite DMS'},
    ]

    for record in records:
        org = Organization.query.filter_by(name=record['name']).first()
        if not org:
            org = Organization(name=record['name'],
                               url=record['url'],
                               logo_url=record['logo_url'],
                               client_portal=record['client_portal'],
                               app_name=record['app_name'])
            db.session.add(org)
            db.session.commit()
