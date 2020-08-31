
import uuid
import datetime

from app.main import db
from app.main.core.rac import RACMgr, RACRoles
from app.main.model.user import User, Department
from app.main.seed.sales_board import create_sales_boards

role_records = None


def seed_users_with_roles():
    # Service Dept
    svc_mgr_email = 'peterp.dstar@localhost.com'
    svc_mgr = User.query.filter_by(email=svc_mgr_email).first()
    if not svc_mgr:
        svc_mgr = User(
            public_id=str(uuid.uuid4()),
            email=svc_mgr_email,
            username= 'peterp',
            password= 'password',
            first_name= 'Peter',
            last_name= 'Piper',
            title= 'Service Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SERVICE.name,
            registered_on= datetime.datetime.utcnow()
        )
        svc_mgr = RACMgr.assign_role_to_user(RACRoles.SERVICE_MGR, svc_mgr)
        db.session.add(svc_mgr)
    svc_mgr.language = 'ENGLISH'
    

    svc_rep_email = 'frankf.dstar@localhost.com'
    svc_rep = User.query.filter_by(email=svc_rep_email).first()
    if not svc_rep:
        svc_rep = User(
            public_id=str(uuid.uuid4()),
            email=svc_rep_email,
            username= 'frankf',
            password= 'password',
            first_name= 'Frank',
            last_name= 'Fallor',
            title= 'Service Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SERVICE.name,
            registered_on= datetime.datetime.utcnow()
        )
        svc_rep = RACMgr.assign_role_to_user(RACRoles.SERVICE_REP, svc_rep)
        db.session.add(svc_rep)
    svc_rep.language = 'ENGLISH'

    svc_mgr_email2 = 'servicemanager.dstar@localhost.com'
    svc_mgr2 = User.query.filter_by(email=svc_mgr_email2).first()
    if not svc_mgr2:
        svc_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=svc_mgr_email2,
            username= 'servicemanager',
            password= 'password',
            first_name= 'Larry',
            last_name= 'King',
            title= 'Service Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SERVICE.name,
            registered_on= datetime.datetime.utcnow()
        )
        svc_mgr2 = RACMgr.assign_role_to_user(RACRoles.SERVICE_MGR, svc_mgr2)
        db.session.add(svc_mgr2)
    svc_mgr2.language = 'ENGLISH'

    svc_admin_email = 'serviceadmin.dstar@localhost.com'
    svc_admin = User.query.filter_by(email=svc_admin_email).first()
    if not svc_admin:
        svc_admin = User(
            public_id=str(uuid.uuid4()),
            email=svc_admin_email,
            username= 'serviceadmin',
            password= 'password',
            first_name= 'Hillary',
            last_name= 'Trump',
            title= 'Service Admin',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SERVICE.name,
            registered_on= datetime.datetime.utcnow()
        )
        svc_admin = RACMgr.assign_role_to_user(RACRoles.SERVICE_MGR, svc_admin)
        db.session.add(svc_admin)
    svc_admin.language = 'ENGLISH'

    svc_rep_email2 = 'servicerep.dstar@localhost.com'
    svc_rep2 = User.query.filter_by(email=svc_rep_email2).first()
    if not svc_rep2:
        svc_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=svc_rep_email2,
            username= 'servicerep',
            password= 'password',
            first_name= 'John',
            last_name= 'Roosvelt',
            title= 'Service Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SERVICE.name,
            registered_on= datetime.datetime.utcnow()
        )
        svc_rep2 = RACMgr.assign_role_to_user(RACRoles.SERVICE_REP, svc_rep2)
        db.session.add(svc_rep2)
    svc_rep2.language = 'ENGLISH'

    # Sales Dept
    sales_mgr_email = 'jennyj.dstar@localhost.com'
    sales_mgr = User.query.filter_by(email=sales_mgr_email).first()
    if not sales_mgr:
        sales_mgr = User(
            public_id=str(uuid.uuid4()),
            email=sales_mgr_email,
            username= 'jennyj',
            password= 'password',
            first_name= 'Jenny',
            last_name= 'Jones',
            title= 'Sales Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SALES.name,
            registered_on= datetime.datetime.utcnow()
        )
        sales_mgr = RACMgr.assign_role_to_user(RACRoles.SALES_MGR, sales_mgr)
        db.session.add(sales_mgr)
    sales_mgr.language = 'ENGLISH'

    sales_rep_email = 'mom.dstar@localhost.com'
    sales_rep = User.query.filter_by(email=sales_rep_email).first()
    if not sales_rep:
        sales_rep = User(
            public_id=str(uuid.uuid4()),
            email=sales_rep_email,
            username= 'mom',
            password= 'password',
            first_name= 'Mo',
            last_name= 'Mahmed',
            title= 'Sales Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SALES.name,
            registered_on= datetime.datetime.utcnow()
        )
        sales_rep = RACMgr.assign_role_to_user(RACRoles.SALES_REP, sales_rep)
        db.session.add(sales_rep)
    sales_rep.language = 'ENGLISH'

    sales_mgr_email2 = 'salemanager.dstar@localhost.com'
    sales_mgr2 = User.query.filter_by(email=sales_mgr_email2).first()
    if not sales_mgr2:
        sales_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=sales_mgr_email2,
            username= 'salemanager',
            password= 'password',
            first_name= 'Gwen',
            last_name= 'Palid',
            title= 'Sales Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SALES.name,
            registered_on= datetime.datetime.utcnow()
        )
        sales_mgr2 = RACMgr.assign_role_to_user(RACRoles.SALES_MGR, sales_mgr2)
        db.session.add(sales_mgr2)
    sales_mgr2.language = 'ENGLISH'

    sales_admin_email = 'salesadmin@localhost.com'
    sales_admin = User.query.filter_by(email=sales_admin_email).first()
    if not sales_admin:
        sales_admin = User(
            public_id=str(uuid.uuid4()),
            email=sales_admin_email,
            username= 'kimy',
            password= 'password',
            first_name= 'Kim',
            last_name= 'Yuno',
            title= 'Sales Admin',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SALES.name,
            registered_on= datetime.datetime.utcnow()
        )
        sales_admin = RACMgr.assign_role_to_user(RACRoles.SALES_ADMIN, sales_admin)
        db.session.add(sales_admin)
    sales_admin.language = 'ENGLISH'

    sales_rep_email2 = 'salesrep.dstar@localhost.com'
    sales_rep2 = User.query.filter_by(email=sales_rep_email2).first()
    if not sales_rep2:
        sales_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=sales_rep_email2,
            username= 'salesrep',
            password= 'password',
            first_name= 'Peter',
            last_name= 'Otoole',
            title= 'Sales Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.SALES.name,
            registered_on= datetime.datetime.utcnow()
        )
        sales_rep2 = RACMgr.assign_role_to_user(RACRoles.SALES_REP, sales_rep2)
        db.session.add(sales_rep2)
    sales_rep2.language = 'ENGLISH'

    # Opener Dept
    opener_mgr_email = 'erice.dstar@localhost.com'
    opener_mgr = User.query.filter_by(email=opener_mgr_email).first()
    if not opener_mgr:
        opener_mgr = User(
            public_id=str(uuid.uuid4()),
            email=opener_mgr_email,
            username= 'erice',
            password= 'password',
            first_name= 'Eric',
            last_name= 'Erikson',
            title= 'Opener Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.OPENERS.name,
            registered_on= datetime.datetime.utcnow()
        )
        opener_mgr = RACMgr.assign_role_to_user(RACRoles.OPENER_MGR, opener_mgr)
        db.session.add(opener_mgr)
    opener_mgr.language = 'ENGLISH'

    opener_rep_email = 'blankab.dstar@localhost.com'
    opener_rep = User.query.filter_by(email=opener_rep_email).first()
    if not opener_rep:
        opener_rep = User(
            public_id=str(uuid.uuid4()),
            email=opener_rep_email,
            username= 'blankab',
            password= 'password',
            first_name= 'Blanca',
            last_name= 'Bower',
            title= 'Opener Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.OPENERS.name,
            registered_on= datetime.datetime.utcnow()
        )
        opener_rep = RACMgr.assign_role_to_user(RACRoles.OPENER_REP, opener_rep)
        db.session.add(opener_rep)
    opener_rep.language = 'ENGLISH'

    opener_mgr_email2 = 'openermanager.dstar@localhost.com'
    opener_mgr2 = User.query.filter_by(email=opener_mgr_email2).first()
    if not opener_mgr2:
        opener_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=opener_mgr_email2,
            username= 'openermanager',
            password= 'password',
            first_name= 'John',
            last_name= 'Snow',
            title= 'Opener Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.OPENERS.name,
            registered_on= datetime.datetime.utcnow()
        )
        opener_mgr2 = RACMgr.assign_role_to_user(RACRoles.OPENER_MGR, opener_mgr2)
        db.session.add(opener_mgr2)
    opener_mgr2.language = 'ENGLISH'

    opener_rep_email2 = 'openerrep.dstar@localhost.com'
    opener_rep2 = User.query.filter_by(email=opener_rep_email2).first()
    if not opener_rep2:
        opener_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=opener_rep_email2,
            username= 'openerrep',
            password= 'password',
            first_name= 'Ragnar',
            last_name= 'Lothbrook',
            title= 'Opener Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.OPENERS.name,
            registered_on= datetime.datetime.utcnow()
        )
        opener_rep2 = RACMgr.assign_role_to_user(RACRoles.OPENER_REP, opener_rep2)
        db.session.add(opener_rep2)
    opener_rep2.language = 'ENGLISH'

    # Doc Process Dept
    doc_process_mgr_email = 'tonyt.dstar@localhost.com'
    doc_process_mgr = User.query.filter_by(email=doc_process_mgr_email).first()
    if not doc_process_mgr:
        doc_process_mgr = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_mgr_email,
            username= 'tonyt',
            password= 'password',
            first_name= 'Tony',
            last_name= 'Tenor',
            title= 'Doc Process Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.DOCPROC.name,
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_mgr = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_MGR, doc_process_mgr)
        db.session.add(doc_process_mgr)
    doc_process_mgr.language = 'ENGLISH'

    doc_process_rep_email = 'billyb.dstar@localhost.com'
    doc_process_rep = User.query.filter_by(email=doc_process_rep_email).first()
    if not doc_process_rep:
        doc_process_rep = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_rep_email,
            username= 'billyb',
            password= 'password',
            first_name= 'Billy',
            last_name= 'Blanks',
            title= 'Doc Process Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.DOCPROC.name,
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_rep = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_REP, doc_process_rep)
        db.session.add(doc_process_rep)
    doc_process_rep.language = 'ENGLISH'
    
    doc_process_mgr_email2 = 'docmanager.dstar@localhost.com'
    doc_process_mgr2 = User.query.filter_by(email=doc_process_mgr_email2).first()
    if not doc_process_mgr2:
        doc_process_mgr2 = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_mgr_email2,
            username= 'docmanager',
            password= 'password',
            first_name= 'Monica',
            last_name= 'Rowanda',
            title= 'Doc Process Manager',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.DOCPROC.name,
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_mgr2 = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_MGR, doc_process_mgr2)
        db.session.add(doc_process_mgr2)
    doc_process_mgr2.language = 'ENGLISH'

    doc_process_rep_email2 = 'docrep.dstar@localhost.com'
    doc_process_rep2 = User.query.filter_by(email=doc_process_rep_email2).first()
    if not doc_process_rep2:
        doc_process_rep2 = User(
            public_id=str(uuid.uuid4()),
            email=doc_process_rep_email2,
            username= 'docrep',
            password= 'password',
            first_name= 'Lagatha',
            last_name= 'Lothbrook',
            title= 'Doc Process Rep',
            language='ENGLISH',
            personal_phone='',
            voip_route_number='',
            department=Department.DOCPROC.name,
            registered_on= datetime.datetime.utcnow()
        )
        doc_process_rep2 = RACMgr.assign_role_to_user(RACRoles.DOC_PROCESS_REP, doc_process_rep2)
        db.session.add(doc_process_rep2)
    doc_process_rep2.language = 'ENGLISH'
    
    db.session.commit()

    # create sales boards for all sales department users
    create_sales_boards()
    

### resource based permissions

from app.main.model.rac import RACResource, RACPermission, RACRole
def seed_permissions():
    ## Non admin API resources
    ## Allowed fror Admin roles
    resources = [
        {'name': 'candidates.create', 'desc': 'Create Candidate', 'roles': [ RACRoles.OPENER_MGR, RACRoles.OPENER_REP ]},
        {'name': 'candidates.update', 'desc': 'Update Candidate', 'roles': [ RACRoles.OPENER_MGR, RACRoles.OPENER_REP ]},
        {'name': 'candidates.delete', 'desc': 'Delete Candidate', 'roles': [ RACRoles.OPENER_MGR ]},
        {'name': 'candidates.view', 'desc': 'View Candidate', 'roles': [RACRoles.OPENER_MGR, RACRoles.OPENER_REP, RACRoles.SALES_MGR] },
        # appointments
        {'name': 'appointments.create', 'desc': 'Create Appointment', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        {'name': 'appointments.update', 'desc': 'Update Appointment', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        {'name': 'appointments.delete', 'desc': 'Delete Appointment',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        {'name': 'appointments.view', 'desc': 'View Appointment',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        # leads
        {'name': 'leads.create', 'desc': 'Create Lead',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        {'name': 'leads.update', 'desc': 'Update Lead',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        {'name': 'leads.delete', 'desc': 'Delete Lead',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        {'name': 'leads.view', 'desc': 'View Lead',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP, ]},
        {'name': 'leads.assignment', 'desc': 'Assign the Lead',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN,  RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN,  ]},
        # leads credit report & debts
        {'name': 'leads.debts.create', 'desc': 'Add Debts for Lead', 
          'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'leads.debts.update', 'desc': 'Update Debts for Lead', 
          'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'leads.debts.delete', 'desc': 'Delete Debts for Lead', 
          'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'leads.debts.view', 'desc': 'View Debts for Lead', 
          'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        # payment contract
        {'name': 'leads.contract.create', 'desc': 'Add payment contract', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'leads.contract.update', 'desc': 'Update payment contract', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'leads.contract.view', 'desc': 'View payment contract', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'leads.contract.send', 'desc': 'View payment contract', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        # clients
        {'name': 'clients.create', 'desc': 'Create Client', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.update', 'desc': 'Update Client',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.delete', 'desc': 'Delete Client',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.view', 'desc': 'View Client', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.assignment', 'desc': 'Client Assignment', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, ]},
        {'name': 'clients.debts.view', 'desc': 'View Client debts', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.debts.update', 'desc': 'Update Client debts', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.debts.create', 'desc': 'Create Client debts', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        # client service schedule
        {'name': 'clients.service_schedule.view', 'desc': 'View client service Schedule', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.service_schedule.update', 'desc': 'Update client service schedule', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.service_schedule.create', 'desc': 'Create client service Schedule', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        # client documents
        {'name': 'clients.docs.view', 'desc': 'View client documents', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,
                   RACRoles.DOC_PROCESS_MGR, RACRoles.DOC_PROCESS_REP]},
        {'name': 'clients.docs.update', 'desc': 'Update client documents', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,
                   RACRoles.DOC_PROCESS_MGR, RACRoles.DOC_PROCESS_REP]},
        {'name': 'clients.docs.create', 'desc': 'Create client documents', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,
                   RACRoles.DOC_PROCESS_MGR, RACRoles.DOC_PROCESS_REP]},
        # amendment
        {'name': 'clients.amendment.create', 'desc': 'Create contract amendment', 
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.amendment.update', 'desc': 'Update contract amendment',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.amendment.view', 'desc': 'View amendment',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'clients.amendment.request', 'desc': 'Approve request(TR) for amendment',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        # team request
        {'name': 'clients.tr.view', 'desc': 'Clients Team requests',
         'roles': [RACRoles.SALES_MGR, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, ]},
        {'name': 'tr.view', 'desc': 'Team requests view',
         'roles': [RACRoles.SALES_MGR, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, ]},
        {'name': 'tr.update', 'desc': 'Team requests update',
         'roles': [RACRoles.SALES_MGR, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, ]},
        {'name': 'teams.view', 'desc': 'Teams view',
         'roles': [RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, ]},
        {'name': 'teams.create', 'desc': 'Teams view',
         'roles': []},
        {'name': 'teams.update', 'desc': 'Teams view',
         'roles': []},
        # tasks
        {'name': 'tasks.view', 'desc': 'View tasks',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'tasks.create', 'desc': 'Create tasks',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        {'name': 'tasks.update', 'desc': 'Update tasks',
         'roles': [RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SALES_REP, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN, RACRoles.SERVICE_REP,]},
        # collectors
        {'name': 'collectors.view', 'desc': 'View Collectors',
         'roles': [RACRoles.DOC_PROCESS_MGR, RACRoles.DOC_PROCESS_REP]},
        {'name': 'collectors.create', 'desc': 'Create Collectors',
         'roles': [RACRoles.DOC_PROCESS_MGR, RACRoles.DOC_PROCESS_REP]},
        {'name': 'collectors.update', 'desc': 'Update Collectors',
         'roles': [RACRoles.DOC_PROCESS_MGR, RACRoles.DOC_PROCESS_REP]},
        # campaigns
        {'name': 'campaigns.view', 'desc': 'View Campaigns',
         'roles': [RACRoles.OPENER_MGR, RACRoles.SALES_MGR, RACRoles.SERVICE_MGR]},
        {'name': 'campaigns.create', 'desc': 'Create Campaigns',
         'roles': [RACRoles.OPENER_MGR, RACRoles.SALES_MGR, RACRoles.SERVICE_MGR]},
        {'name': 'campaigns.update', 'desc': 'Update Campaigns',
         'roles': [RACRoles.OPENER_MGR, RACRoles.SALES_MGR, RACRoles.SERVICE_MGR]},
        # users view
        {'name': 'users.view', 'desc': 'View Users',
         'roles': [RACRoles.OPENER_MGR, RACRoles.SALES_MGR, RACRoles.SALES_ADMIN, RACRoles.SERVICE_MGR, RACRoles.SERVICE_ADMIN]},
        {'name': 'users.create', 'desc': 'Create Users',
         'roles': []},
        {'name': 'users.update', 'desc': 'Update Users',
         'roles': []},

    ]

    # clean up the resources
    for rac_resource in RACResource.query.all():
        db.session.delete(rac_resource)
    db.session.commit()

    for res in resources:
        rac_resource = RACResource(name=res['name'],
                                   description=res['desc'])
        db.session.add(rac_resource)
        db.session.commit()

        # add roles
        for role in res['roles']:
            rac_role = RACRole.query.filter_by(name=role.value).first()
            perm = RACPermission(rac_role_id=rac_role.id,
                                 resource_id=rac_resource.id) 
            db.session.add(perm)

        # admin & super admin
        superadmin_role = RACRole.query.filter_by(name=RACRoles.SUPER_ADMIN.value).first()
        admin_role = RACRole.query.filter_by(name=RACRoles.ADMIN.value).first()
        su_perm = RACPermission(rac_role_id=superadmin_role.id,
                                 resource_id=rac_resource.id) 
        db.session.add(su_perm)
        perm = RACPermission(rac_role_id=admin_role.id,
                             resource_id=rac_resource.id) 
        db.session.add(perm)
        db.session.commit()
