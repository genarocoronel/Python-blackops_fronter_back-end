import uuid
import datetime
from app.main import db
from app.main.model.task import ScrapeTask
from app.main.model.credit_report_account import CreditReportData, CreditReportAccount
from app.main.model.collector import DebtCollector

def scrape_credit_report(account: CreditReportAccount, task_message='Capture credit report debts'):
    """ Pulls credit report debts by queueing scrape job """
    task = account.launch_spider(
        'capture',
        task_message
    )
    save_changes(task)

    resp = {
        'message': 'Spider queued',
        'task_id': task.id
    }

    return resp


def check_existing_scrape_task(account):
    task = ScrapeTask.query.filter_by(
        account_id=account.id, complete=False).first()

    if not task:
        return False, None

    response_object = {
        'success': False,
        'message': 'Existing fetch ongoing for this candidate'
    }
    return True, response_object


def get_report_data(account, data_public_id=None):
    if not account:
        return []

    if data_public_id:
        return CreditReportData.query.filter_by(account_id=account.id, public_id=data_public_id).first()

    return CreditReportData.query.filter_by(account_id=account.id).all()


def save_new_debt(data, account):
    # debt collectors
    coll_id = None 

    collector_name = data.get('collector_name')
    if collector_name:
        dc = DebtCollector.query.filter_by(name=collector_name).first()
        if not dc:
            dc = DebtCollector(public_id=str(uuid.uuid4()),
                               name=collector_name,
                               phone=data.get('collector_phone'),
                               fax=data.get('collector_fax'),
                               address=data.get('collector_address'),
                               city=data.get('collector_city'),
                               state=data.get('collector_state'),
                               zip_code=data.get('collector_state'),
                               inserted_on=datetime.datetime.utcnow(),
                               updated_on=datetime.datetime.utcnow())
            db.session.add(dc)
            db.session.commit()

        coll_id = dc.id

    debt_data = CreditReportData(
        account_id=account.id,
        public_id=str(uuid.uuid4()),
        debt_name=data.get('debt_name'),
        creditor=data.get('creditor'),
        ecoa=data.get('ecoa'),
        account_number=data.get('account_number'),
        collector_ref_no=data.get('collector_ref_no'),
        account_type=data.get('account_type'),
        push=data.get('push'),
        collector_id=coll_id,
        last_debt_status=data.get('last_debt_status'),
        bureaus=data.get('bureaus'),
        days_delinquent=data.get('days_delinquent'),
        balance_original=data.get('balance_original'),
        payment_amount=data.get('payment_amount'),
        credit_limit=data.get('credit_limit'),
        graduation=data.get('graduation'),
        last_update=data.get('last_update') if 'last_update' in data else datetime.datetime.utcnow(),
        enrolled_date=datetime.datetime.utcnow(), 
    )
    save_changes(debt_data)
    return debt_data


def update_debt(data):
    debt_data = CreditReportData.query.filter_by(public_id=data['public_id']).first()
    if debt_data:
        # check for collector information
        collector_id = data.get('collector_id')
        if collector_id:
            dc = DebtCollector.query.filter_by(public_id=collector_id).first()
            if not dc:
                dc = DebtCollector(public_id=str(uuid.uuid4()),
                                   name=data.get('collector_name'),
                                   phone=data.get('collector_phone'),
                                   fax=data.get('collector_fax'),
                                   address=data.get('collector_address'),
                                   city=data.get('collector_city'),
                                   state=data.get('collector_state'),
                                   zip_code=data.get('collector_zip_code'),
                                   inserted_on=datetime.datetime.utcnow(),
                                   updated_on=datetime.datetime.utcnow())
                db.session.add(dc)
                db.session.commit()
           
            # debt collector has changed
            if debt_data.collector_id and debt_data.collector_id != dc.id:
                debt_data.prev_collector_id = debt_data.collector_id 
            debt_data.collector_id = dc.id
            # remove collector id from the update list
            del data['collector_id']

        # remove attrs not updated
        del data['public_id']
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

def add_credit_report_data(data, account):
    for item in data:
        save_new_debt(item, account)

    response_object = {
            'success': True,
            'message': 'Debts Added successfully',
        }
    return response_object

def delete_debts(ids):
    debt_datas = CreditReportData.query.filter(CreditReportData.public_id.in_(ids)).all()
    for c in debt_datas:
        db.session.delete(c)
        db.session.commit()
    return

def push_debts(ids, push_type):
    debt_datas = CreditReportData.query.filter(CreditReportData.public_id.in_(ids)).all()
    for debt_data in debt_datas:
        debt_data.push = push_type
    db.session.commit()
