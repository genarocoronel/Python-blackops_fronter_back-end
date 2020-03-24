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

    svc_mgr_email2 = 'servicemanager.dstar@localhost.com'
    existing_svc_mgr_usr2 = User.query.filter_by(email=svc_mgr_email2).first()
    if not existing_svc_mgr_usr2:
        svc_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=svc_mgr_email2,
            username= 'servicemanager',
            password= 'password',
            first_name= 'Larry',
            last_name= 'King',
            title= 'Service Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        svc_mgr2 = RACMgr.assign_role_to_user(RACRoles.SERVICE_MGR, svc_mgr2)
        db.session.add(svc_mgr2)

    svc_rep_email2 = 'servicerep.dstar@localhost.com'
    existing_svc_rep_usr2 = User.query.filter_by(email=svc_rep_email2).first()
    if not existing_svc_rep_usr2:
        svc_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=svc_rep_email2,
            username= 'servicerep',
            password= 'password',
            first_name= 'John',
            last_name= 'Roosvelt',
            title= 'Service Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        svc_rep2 = RACMgr.assign_role_to_user(RACRoles.SERVICE_REP, svc_rep2)
        db.session.add(svc_rep2)

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

    sales_mgr_email2 = 'salemanager.dstar@localhost.com'
    existing_sales_mgr_usr2 = User.query.filter_by(email=sales_mgr_email2).first()
    if not existing_sales_mgr_usr2:
        sales_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=sales_mgr_email2,
            username= 'salemanager',
            password= 'password',
            first_name= 'Gwen',
            last_name= 'Palid',
            title= 'Sales Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        sales_mgr2 = RACMgr.assign_role_to_user(RACRoles.SALES_MGR, sales_mgr2)
        db.session.add(sales_mgr2)

    sales_rep_email2 = 'salesrep.dstar@localhost.com'
    existing_sales_rep_usr2 = User.query.filter_by(email=sales_rep_email2).first()
    if not existing_sales_rep_usr2:
        sales_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=sales_rep_email2,
            username= 'salesrep',
            password= 'password',
            first_name= 'Peter',
            last_name= 'Otoole',
            title= 'Sales Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        sales_rep2 = RACMgr.assign_role_to_user(RACRoles.SALES_REP, sales_rep2)
        db.session.add(sales_rep2)

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

    opener_mgr_email2 = 'openermanager.dstar@localhost.com'
    existing_opener_mgr_usr2 = User.query.filter_by(email=opener_mgr_email2).first()
    if not existing_opener_mgr_usr2:
        opener_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=opener_mgr_email2,
            username= 'openermanager',
            password= 'password',
            first_name= 'John',
            last_name= 'Snow',
            title= 'Opener Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        opener_mgr2 = RACMgr.assign_role_to_user(RACRoles.OPENER_MGR, opener_mgr2)
        db.session.add(opener_mgr2)

    opener_rep_email2 = 'openerrep.dstar@localhost.com'
    existing_opener_rep_usr2 = User.query.filter_by(email=opener_rep_email2).first()
    if not existing_opener_rep_usr2:
        opener_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=opener_rep_email2,
            username= 'openerrep',
            password= 'password',
            first_name= 'Ragnar',
            last_name= 'Lothbrook',
            title= 'Opener Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        opener_rep2 = RACMgr.assign_role_to_user(RACRoles.OPENER_REP, opener_rep2)
        db.session.add(opener_rep2)

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
    
    doc_process_mgr_email2 = 'docmanager.dstar@localhost.com'
    existing_doc_process_mgr_usr2 = User.query.filter_by(email=doc_process_mgr_email2).first()
    if not existing_doc_process_mgr_usr2:
        doc_process_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_mgr_email2,
            username= 'docmanager',
            password= 'password',
            first_name= 'Monica',
            last_name= 'Rowanda',
            title= 'Doc Process Manager',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_mgr2 = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_MGR, doc_process_mgr2)
        db.session.add(doc_process_mgr2)

    doc_process_rep_email2 = 'docrep.dstar@localhost.com'
    existing_doc_process_rep_usr2 = User.query.filter_by(email=doc_process_rep_email2).first()
    if not existing_doc_process_rep_usr2:
        doc_process_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_rep_email2,
            username= 'docrep',
            password= 'password',
            first_name= 'Lagatha',
            last_name= 'Lothbrook',
            title= 'Doc Process Rep',
            language='en',
            personal_phone='',
            voip_route_number='',
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_rep2 = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_REP, doc_process_rep2)
        db.session.add(doc_process_rep2)
    
    db.session.commit()