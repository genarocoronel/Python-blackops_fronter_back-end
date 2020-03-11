from app.main.core.rac import RACRoles
from app.main.model.user import User
from app.main.service.user_service import save_new_user


def create_super_admin():
    super_admin_email = 'admin@localhost.com'

    existing_super_admin = User.query.filter_by(email=super_admin_email).first()
    if not existing_super_admin:
        super_admin = {
            'email': super_admin_email,
            'username': 'admin',
            'password': 'password',
            'first_name': 'Administrator',
            'last_name': 'System Account',
            'title': 'Super Administrator',
            'language': 'en',
            'personal_phone': '',
            'voip_route_number': ''
        }
        save_new_user(super_admin, RACRoles.SUPER_ADMIN)
