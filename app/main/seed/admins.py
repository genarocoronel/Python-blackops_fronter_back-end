from app.main import db
from app.main.core.rac import RACRoles, RACMgr
from app.main.model.user import User
from app.main.service.user_service import save_new_user


def create_super_admin(email='admin@localhost.com', password='password'):
    existing_super_admin = User.query.filter_by(email=email).first()
    if not existing_super_admin:
        super_admin = {
            'email': email,
            'username': 'admin',
            'password': password,
            'first_name': 'Administrator',
            'last_name': 'System Account',
            'title': 'Super Administrator',
            'language': 'ENGLISH',
            'personal_phone': '',
            'voip_route_number': '',
        }
        save_new_user(super_admin, RACRoles.SUPER_ADMIN)

        # currently requires use of "print" to write to console for capture
        print(
            f'########  IMPORTANT  ########\nCreating Admin Login\nusername: {email} \npassword: {password}\n#############################')

    elif existing_super_admin and existing_super_admin.role is None:
        existing_super_admin = RACMgr.assign_role_to_user(RACRoles.SUPER_ADMIN, existing_super_admin)
        existing_super_admin.language = 'ENGLISH'
        db.session.add(existing_super_admin)
        db.session.commit()

