import datetime
import uuid

from app.main.model.rac import RACRole
from app.main import db

def seed_rac_roles():
    """ Seeds RAC Roles """
    roles_seed = [
        {
            'name': 'super_admin',
            'name_friendly': 'Super Admin',
            'description': 'Super Administrator Role'
        },
        {
            'name': 'admin',
            'name_friendly': 'Admin',
            'description': 'Administrator Role'
        },
        {
            'name': 'opener_rep',
            'name_friendly': 'Opener Rep',
            'description': 'Opener Representative Role'
        },
        {
            'name': 'opener_mgr',
            'name_friendly': 'Opener Mgr',
            'description': 'Opener Manager Role'
        },
        {
            'name': 'sales_rep',
            'name_friendly': 'Sales Rep',
            'description': 'Sales Representative Role'
        },
        {
            'name': 'sales_mgr',
            'name_friendly': 'Sales Mgr',
            'description': 'Sales Manager Role'
        },
        {
            'name': 'service_rep',
            'name_friendly': 'Service Rep',
            'description': 'Service Representative Role'
        },
        {
            'name': 'service_mgr',
            'name_friendly': 'Service Mgr',
            'description': 'Service Manager Role'
        },
        {
            'name': 'doc_process_rep',
            'name_friendly': 'Doc Process Rep',
            'description': 'Doc Process Representative Role'
        },
        {
            'name': 'doc_process_mgr',
            'name_friendly': 'Doc Process Mgr',
            'description': 'Doc Process Manager Role'
        },
    ]

    for role_item in roles_seed:
        existing_role = RACRole.query.filter_by(name=role_item['name']).first()
        if not existing_role:
            new_role = RACRole(
                public_id= str(uuid.uuid4()),
                name= role_item['name'],
                name_friendly= role_item['name_friendly'],
                description= role_item['description'],
                inserted_on= datetime.datetime.utcnow(),
                updated_on= datetime.datetime.utcnow()
            )
            db.session.add(new_role)

    db.session.commit()