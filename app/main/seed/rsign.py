from app.main import db
from app.main.model.credit_report_account import CreditPaymentPlan
from app.main.tasks.docusign import sync_templates

from flask import current_app as app

def populate_credit_payment_plan():
    try:
        plan = CreditPaymentPlan(name='Universal',
                                 enrolled_percent=33,
                                 monthly_bank_fee=10,
                                 minimum_fee=2475,
                                 monitoring_fee_1signer=59,
                                 monitoring_fee_2signer=89)
        db.session.add(plan)
        db.session.commit()
    except Exception as err:
        #app.logger.warning("Error in popuating credit payment plan {}".format(str(err)))
        db.session.rollback()


def seed_rsign_records():
    # populate credit payment plan
    populate_credit_payment_plan()
    app.logger.info("Successfully Populated credit payment plan table")
    
    # Syncronize template information from docusign server
    sync_templates()
    app.logger.info("Successfully synced template information from Docusign server")
