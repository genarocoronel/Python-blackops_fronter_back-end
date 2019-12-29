# admin backend
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_basicauth import BasicAuth


# admin models
from app.main.model.client import Client, ClientDisposition
from app.main.model.docsign import DocusignTemplate, DocusignSession
from app.main.model.credit_report_account import CreditReportAccount, CreditReportData, CreditPaymentPlan
from app.main.model.bank_account import BankAccount
	
from app.main.model.debt_payment import DebtPaymentSchedule, DebtPaymentTransaction
"""
Register admin views with the application
"""
def register_admin_views(app, db):
    admin = Admin(app, name='crm', template_mode='bootstrap3')
    admin.add_view(ModelView(Client, db.session))
    admin.add_view(ModelView(ClientDisposition, db.session))
    admin.add_view(ModelView(DocusignTemplate, db.session))
    admin.add_view(ModelView(DocusignSession, db.session))
    admin.add_view(ModelView(BankAccount, db.session))
    admin.add_view(ModelView(CreditReportAccount, db.session))
    admin.add_view(ModelView(CreditReportData, db.session))
    admin.add_view(ModelView(CreditPaymentPlan, db.session))
    admin.add_view(ModelView(DebtPaymentSchedule, db.session))
    admin.add_view(ModelView(DebtPaymentTransaction, db.session))
