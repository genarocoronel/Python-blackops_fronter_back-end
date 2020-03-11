import datetime
import uuid

from app.main import db
from app.main.core.rac import RACMgr, RACRoles
from app.main.model.user import User

role_records = None

def seed_users_with_roles():
    # If the existing Super Admin does not have a RAC Role 
    existing_super_admin = User.query.filter_by(email='admin@localhost.com').first()
    if existing_super_admin and existing_super_admin.role == None:
        existing_super_admin = RACMgr.assign_role_to_user(RACRoles.SUPER_ADMIN, existing_super_admin)
        db.session.add(existing_super_admin)

    # Service Dept
    svc_mgr_email = 'peterp.dstar@localhost.com'
    existing_svc_mgr_usr = User.query.filter_by(email=svc_mgr_email).first()
    if not existing_svc_mgr_usr:
        svc_mgr = User(
            public_id=str(uuid.uuid4()),
            email=svc_mgr_email,
            username= 'peterp',
            password= 'password',
            first_name= 'Peter',
            last_name= 'Piper',
            title= 'Service Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        svc_mgr = RACMgr.assign_role_to_user(RACRoles.SERVICE_MGR, svc_mgr)
        db.session.add(svc_mgr)

    svc_rep_email = 'frankf.dstar@localhost.com'
    existing_svc_rep_usr = User.query.filter_by(email=svc_rep_email).first()
    if not existing_svc_rep_usr:
        svc_rep = User(
            public_id=str(uuid.uuid4()),
            email=svc_rep_email,
            username= 'frankf',
            password= 'password',
            first_name= 'Frank',
            last_name= 'Fallor',
            title= 'Service Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        svc_rep = RACMgr.assign_role_to_user(RACRoles.SERVICE_REP, svc_rep)
        db.session.add(svc_rep)

    # Sales Dept
    sales_mgr_email = 'jennyj.dstar@localhost.com'
    existing_sales_mgr_usr = User.query.filter_by(email=sales_mgr_email).first()
    if not existing_sales_mgr_usr:
        sales_mgr = User(
            public_id=str(uuid.uuid4()),
            email=sales_mgr_email,
            username= 'jennyj',
            password= 'password',
            first_name= 'Jenny',
            last_name= 'Jones',
            title= 'Sales Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        sales_mgr = RACMgr.assign_role_to_user(RACRoles.SALES_MGR, sales_mgr)
        db.session.add(sales_mgr)

    sales_rep_email = 'mom.dstar@localhost.com'
    existing_sales_rep_usr = User.query.filter_by(email=sales_rep_email).first()
    if not existing_sales_rep_usr:
        sales_rep = User(
            public_id=str(uuid.uuid4()),
            email=sales_rep_email,
            username= 'mom',
            password= 'password',
            first_name= 'Mo',
            last_name= 'Mahmed',
            title= 'Sales Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        sales_rep = RACMgr.assign_role_to_user(RACRoles.SALES_REP, sales_rep)
        db.session.add(sales_rep)

    # Opener Dept
    opener_mgr_email = 'erice.dstar@localhost.com'
    existing_opener_mgr_usr = User.query.filter_by(email=opener_mgr_email).first()
    if not existing_opener_mgr_usr:
        opener_mgr = User(
            public_id=str(uuid.uuid4()),
            email=opener_mgr_email,
            username= 'erice',
            password= 'password',
            first_name= 'Eric',
            last_name= 'Erikson',
            title= 'Opener Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        opener_mgr = RACMgr.assign_role_to_user(RACRoles.OPENER_MGR, opener_mgr)
        db.session.add(opener_mgr)

    opener_rep_email = 'blankab.dstar@localhost.com'
    existing_opener_rep_usr = User.query.filter_by(email=opener_rep_email).first()
    if not existing_opener_rep_usr:
        opener_rep = User(
            public_id=str(uuid.uuid4()),
            email=opener_rep_email,
            username= 'blankab',
            password= 'password',
            first_name= 'Blanca',
            last_name= 'Bower',
            title= 'Opener Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        opener_rep = RACMgr.assign_role_to_user(RACRoles.OPENER_REP, opener_rep)
        db.session.add(opener_rep)

    # Doc Process Dept
    doc_process_mgr_email = 'tonyt.dstar@localhost.com'
    existing_doc_process_mgr_usr = User.query.filter_by(email=doc_process_mgr_email).first()
    if not existing_doc_process_mgr_usr:
        doc_process_mgr = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_mgr_email,
            username= 'tonyt',
            password= 'password',
            first_name= 'Tony',
            last_name= 'Tenor',
            title= 'Doc Process Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_mgr = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_MGR, doc_process_mgr)
        db.session.add(doc_process_mgr)

    doc_process_rep_email = 'billyb.dstar@localhost.com'
    existing_doc_process_rep_usr = User.query.filter_by(email=doc_process_rep_email).first()
    if not existing_doc_process_rep_usr:
        doc_process_rep = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_rep_email,
            username= 'billyb',
            password= 'password',
            first_name= 'Billy',
            last_name= 'Blanks',
            title= 'Doc Process Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_rep = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_REP, doc_process_rep)
        db.session.add(doc_process_rep)
    
    db.session.commit()