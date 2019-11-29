import uuid
import datetime
from app.main import db
from app.main.model.task import ScrapeTask
from app.main.model.credit_report_account import CreditReportData


def check_existing_scrape_task(account):
    task = ScrapeTask.query.filter_by(
        account_id=account.id, complete=False).first()

    if not task:
        return False, None

    response_object = {
        'success': False,
        'message': 'Existing fetch ongoing for this candidate'
    }
    return True, (response_object, 500)


def get_report_data(account, data_public_id=None):
    if not account:
        return []
    if data_public_id:
        return CreditReportData.query.filter_by(
            account_id=account.id, public_id=data_public_id).first()
    return CreditReportData.query.filter_by(account_id=account.id).all()


def save_new_debt(data, account):
    data['last_update'] = datetime.datetime.utcnow()
    debt_data = CreditReportData(
        account_id=account.id,
        public_id=str(uuid.uuid4()),
        debt_name=data.get('debt_name'),
        creditor=data.get('creditor'),
        ecoa=data.get('ecoa'),
        account_number=data.get('account_number'),
        account_type=data.get('account_type'),
        push=data.get('push'),
        last_collector=data.get('last_collector'),
        collector_account=data.get('collector_account'),
        last_debt_status=data.get('last_debt_status'),
        bureaus=data.get('bureaus'),
        days_delinquent=data.get('days_delinquent'),
        balance_original=data.get('balance_original'),
        payment_amount=data.get('payment_amount'),
        credit_limit=data.get('credit_limit'),
        graduation=data.get('graduation'),
        last_update=data.get('last_update')
    )
    save_changes(debt_data)
    return debt_data


def update_debt(data, account, public_id):
    debt_data = CreditReportData.query.filter_by(public_id=public_id).first()
    if debt_data:
        for attr in data:
            if hasattr(debt_data, attr):
                setattr(debt_data, attr, data.get(attr))
        setattr(debt_data, 'last_update', datetime.datetime.utcnow())

        save_changes(debt_data)

        response_object = {
            'success': True,
            'message': 'Debt updated successfully',
        }
        return response_object, 200
    else:
        response_object = {
            'success': False,
            'message': 'Debt not found',
        }
        return response_object, 404


def save_changes(*data):
    for entry in data:
        db.session.add(entry)
    db.session.commit()
