from app.main.service.user_service import save_new_user


def create_super_admin():
    super_admin = {
        'email': 'admin@localhost.com',
        'username': 'admin',
        'password': 'password',
        'first_name': 'Administrator',
        'last_name': 'System Account',
        'title': 'Super Administrator',
        'language': 'en',
        'personal_phone': '',
        'voip_route_number': ''
    }
    save_new_user(super_admin, True)
