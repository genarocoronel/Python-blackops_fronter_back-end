from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.styles import PatternFill, Alignment
from app.main.core.io import stream_file
from app.main.config import upload_location as report_file_path
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import enum

from .apiservice import has_permissions
from app.main.model.client import Client, ClientType
from app.main.model.user import User
from app.main.model.rac import RACRole
from app.main.core.rac import RACRoles

from flask import current_app as app


class ReportPeriod(enum.Enum):
    CW = 'Current Week'
    CM = 'Current Month'
    LW = 'Last Week'
    LM = 'Last Month' 
    L2M = 'Last Two Month'
    L3M = 'Last Three Month'
    L6M = 'Last Six Month'
    L12M = 'Last twelve month'

class ReportService(object):
    _permissions = []
    _heading = 'Report'
    _thead_bg_color = '0591f5'
    _report_name = 'report.xlsx'
    _report_body = []
    _start = None
    _end = None
    
    def __init__(self, period=None, start=None, end=None):
        # period
        if period:
            self._parse_period(period)
        else:
            if start:
                # date util parsing
                self._start = dt_parse(start)
            if end:
                self._end = dt_parse(end)


    def _parse_period(self, period):
        today = datetime.utcnow().date()
        if period == ReportPeriod.CW.name:
            self._start = today - timedelta(days=today.weekday()) 
        elif period == ReportPeriod.CM.name:
            self._start = today.replace(day=1)
        elif period == ReportPeriod.LW.name:
            self._start = today - timedelta(days=today.weekday()+7)
            self._end = today - timedelta(days=today.weekday()+1)
        elif period == ReportPeriod.LM.name:
            mstart = today.replace(day=1) 
            self._start = mstart - relativedelta(months=1)
            self._end   = mstart - timedelta(days=1) 
        elif period == ReportPeriod.L2M.name:
            mstart = today.replace(day=1)
            self._start = mstart - relativedelta(months=2)
            self._end   = mstart - timedelta(days=1) 
        elif period == ReportPeriod.L3M.name:
            mstart = today.replace(day=1)
            self._start = mstart - relativedelta(months=3)
            self._end   = mstart - timedelta(days=1)
        elif period == ReportPeriod.L6M.name:
            mstart = today.replace(day=1)
            self._start = mstart - relativedelta(months=6)
            self._end   = mstart - timedelta(days=1)
        elif period == ReportPeriod.L12M.name:
            mstart = today.replace(day=1)
            self._start = mstart - relativedelta(months=12)
            self._end   = mstart - timedelta(days=1)

    @has_permissions
    def view(self, data=None):
        return self._records(data)
        
    # only excel is supported
    @has_permissions
    def download(self, data=None, fmt='excel'):
        report_file = self.to_excel(data) 
        return stream_file(report_file_path, report_file, as_attachment=False)	

    @has_permissions
    def to_excel(self, data=None):
        wb = Workbook()         
        ws = wb.active        
        # fill the data
        ws['A1'] = self._heading
        ws['A3'] = 'Report Date:'
        ws['C3'] = datetime.utcnow().strftime('%m/%d/%Y')
        # styling
        ws['A1'].font = Font(bold=True)

        ws.append([])
        headers = self._fields
        headers.insert(0, '')
        ws.append(headers)
        col_head_style = PatternFill(start_color=self._thead_bg_color, end_color=self._thead_bg_color, fill_type = "solid")
        for rows in ws.iter_rows(min_row=5, max_row=5, min_col=1):
            for cell in rows:
                cell.fill = col_head_style
                cell.alignment = Alignment(wrap_text=True,vertical='top') 

        # append the rows 
        row_index = 5
        # call the abstract method the fetch the rows
        rows = self._values(data)
        for row in rows:
            row_index = row_index + 1
            ws.append(row) 
        # save the file
        report_file = "{}/{}".format(report_file_path, self._report_name)
        wb.save(filename=report_file)
        return self._report_name

    def _values(self, data):
        result = []
        records = self._records(data)
        rep = lambda s: '' if s is None else s
        index = 0
        for record in records:
            index = index + 1
            item = [rep(v) for k, v in record.items()]
            item.insert(0, index)
            result.append(item)
        return result

class ClientReportSvc(ReportService):

    @property
    def _fields(self):
        return ['Campaign Name', 'Interest Level', 'First Name', 'Last Name', 'DOB', 
                'Lead Source', 'Disposition', 'Lead Type', 'Salesman', 
                'Account Manager', 'Email', 'Client ID'
                ]

    def _records(self, data):
        try:
            records = []
            filts = []
            if self._start:
                filts.append(func.date(Client.inserted_on)>=self._start)
            if self._end:
                filts.append(func.date(Client.inserted_on)<=self._end)

            filts.append(Client.type != ClientType.coclient)
            query = Client.query
            if len(filts) > 0:
                query = query.filter(and_(*filts))

            clients = query.all()
            for client in clients:
                record = {
                    'campaign_name': '',
                    'interest_level': '',
                    'first_name': client.first_name,
                    'last_name': client.last_name,
                    'dob': client.dob.strftime('%m/%d/%Y') if client.dob else '',
                    'lead_source': client.lead_source,
                    'disposition': client.disposition.value if client.disposition else '',
                    'lead_type': 'Primary',
                    'salesrep': client.sales_rep.full_name if client.sales_rep else '',
                    'account_manager': client.account_manager.full_name if client.account_manager else '',
                    'email': client.email, 
                    'client_id': client.friendly_id,
                } 
                records.append(record)

            return records
        except Exception as err:
            app.logger.warning("Client report service {}".format(str(err)))
            return []
        

class SalesReportSvc(ReportService):
    _heading = 'Sales Report'
    _report_name = 'sales_report.xlsx'
   
    @property
    def _fields(self):
        return ['Agent', 'New Leads', 'New Deals', 'Recycled Leads', 'Recycled Deals', 
                'Closing % Recycled', 'Total Leads All', 'Total Closing % All', 'Retention', 
                'Total Debt' ]
        
    def _records(self, data):
        try:
            records = []
            filts = []
            if self._start:
                filts.append(func.date(Client.inserted_on)>=self._start)
            if self._end:
                filts.append(func.date(Client.inserted_on)<=self._end)
  
            for user in User.query.outerjoin(RACRole).filter(RACRole.name==RACRoles.SALES_REP.value).all():
                lead_query = user.sales_accounts.filter(Client.type==ClientType.lead)
                if len(filts) > 0:
                    lead_query = lead_query.filter(and_(*filts))
                lead_count = lead_query.count()

                deal_query = user.sales_accounts.filter(Client.type==ClientType.client)
                if len(filts) > 0:
                    deal_query = deal_query.filter(and_(*filts))
                deal_count = deal_query.count()
               
                total_debt = 0
                for deal in deal_query.all():
                    total_debt = total_debt + deal.total_debt 

                record = {
                    'name': user.full_name, 
                    'lead_count': lead_count,
                    'deal_count': deal_count,
                    'recycled_lead_count': 0,
                    'recycled_deal_count': 0,
                    'recycled_closing_percent': 0,
                    'total_leads': 0,
                    'total_closing_percent': 0,
                    'retention': 0,
                    'total_debt': total_debt,
                }
                records.append(record)

            return records

        except Exception as err:
            app.logger.warning("Sales report service {}".format(str(err)))
            return []


from app.main.model.debt_payment import DebtPaymentSchedule, DebtEftStatus
class ACHReportSvc(ReportService):
    _heading = 'ACH Report'
    _report_name = 'ach_report.xlsx'
    
    @property
    def _fields(self):
        result = [ 'EPPS EFT Transaction ID', 'Payment Processor', 'Created Date', 'Client ID', 'Amount ($)', 
                  'Description', 'Effective Date', 'EPPS EFT Status', 'EPPS EFT Status Detail', 
                  'EPPS EFT Status Date', 'EPPS Trust Account Balance ($)', 'EPPS Account Holder ID', 
                  'Backend', 'Name Account Owner', 'Routing#', 'Account#', 'Account Type', 'Payment Transaction Id']
        return result
    
    def _records(self, data):
        try:
            records = []
            payment_records = DebtPaymentSchedule.query.filter(DebtPaymentSchedule.status != DebtEftStatus.FUTURE.name).all()
            for payment_record in payment_records:
                # bank account
                client = payment_record.contract.client
                bank_account = client.bank_account
                tr = payment_record.transaction

                record = {
                    'eft_trans_id': tr.trans_id if tr else "",
                    'pymt_processor': 'EPPS',
                    'created_date': tr.created_date.strftime("%m/%d/%Y") if tr else "",
                    'client_id': "{} ({})".format(client.friendly_id, client.full_name),
                    'amount': payment_record.amount,
                    'description': payment_record.desc,
                    'effective_date': payment_record.due_date.strftime("%m/%d/%Y"),
                    'eft_status': tr.status if tr else "",
                    'eft_status_detail': tr.message if tr else "",
                    'eft_status_date': tr.modified_date.strftime("%m/%d/%Y") if tr else "",
                    'trust_account_balance': 0,
                    'account_holder_id': client.epps_account_id,
                    'backend': 'EDMS',
                    'bank_name': bank_account.bank_name,
                    'routing_number': bank_account.routing_number,
                    'account_number': bank_account.account_number,
                    'account_type': 'Checking',
                    'pymt_trans_id': "",  
                }
                records.append(record)

            return records
        
        except Exception as err:
            app.logger.warning("ACH report service {}".format(str(err)))
            return []

class FutureDraftReportSvc(ReportService):
    _heading = 'Future Draft Transactions Report'
    _report_name = 'future_draft_report.xlsx'
    
    @property
    def _fields(self): 
        return ['Client ID', 'Amount($)', 'Description', 'Effective Date', 'Backend']

    def _records(self, data):
        try:
            records = []
            payment_records = DebtPaymentSchedule.query.filter(DebtPaymentSchedule.status == DebtEftStatus.FUTURE.name).all()
            for payment_record in payment_records:
                client = payment_record.contract.client
                friendly_id = client.friendly_id if client.friendly_id else ''
                record = {
                    'client_id': "{}({})".format(friendly_id, client.full_name),
                    'amount': payment_record.amount,
                    'description': payment_record.desc,
                    'effective_date': payment_record.due_date.strftime("%m/%d/%Y"),
                    'backend': 'EDMS',
                }
                records.append(record)

            return records

        except Exception as err:
            app.logger.warning("Future Draf report service {}".format(str(err)))
            return []

from app.main.model.collector import DebtCollector
class CollectorReportSvc(ReportService):
    _heading = 'Debt Collector Report'
    _report_name = 'debt_collector_report.xlsx'

    @property
    def _fields(self):
        return [ 'Collector Name', 'Company Name', 'Contact Phone #', 'Fax Number', 
                 'Number of Debt', 'Created Date', 'Status', 'Notes', 'Last Update' ]

    def _records(self, data):
        try:
            records = []
            query = DebtCollector.query

            collectors = query.all() 
            for collector in collectors:
                num_debts = collector.active_debts.count()
                record = {
                    'name': collector.name,
                    'company_name': '',
                    'phone': collector.phone,
                    'fax': collector.fax,
                    'num_debts': num_debts,
                    'created': collector.inserted_on.strftime('%m/%d/%Y'),
                    'status': 'Active',
                    'notes': '',
                    'modified': collector.updated_on.strftime('%m/%d/%Y'),  
                }
                records.append(record)

            return records

        except Exception as err:
            app.logger.warning("Collector report service {}".format(str(err)))
            return []

from app.main.model.creditor import Creditor
class CreditorReportSvc(ReportService):
    _heading = 'Creditor Management Report'
    _report_name = 'creditors_report.xlsx'

    @property
    def _fields(self):
        return [ 'Creditor Name', 'Company Name', 'Contact Person', 'Contact Phone #', 
                 'Created Date', 'Status', 'Last Update' ]

    def _records(self, data):
        try:
            records = []
            query = Creditor.query

            creditors = query.all() 
            for creditor in creditors:
                record = {
                    'name': creditor.name,
                    'company_name': creditor.company_name,
                    'contact_person': creditor.contact_person,
                    'phone': creditor.phone,
                    'created': creditor.inserted_on.strftime('%m/%d/%Y'),
                    'status': 'Active' if creditor.is_active else 'Inactive',
                    'modified': creditor.updated_on.strftime('%m/%d/%Y'),  
                }
                records.append(record)

            return records

        except Exception as err:
            app.logger.warning("Creditor report service {}".format(str(err)))
            return []

from app.main.model.usertask import UserTask
class TaskReportSvc(ReportService):
    _heading = 'Task Management Report'
    _report_name = 'task_report.xlsx'

    @property
    def _fields(self):
        return [ 'ID', 'Description', 'Status', 'Type', 'Client ID', 'Client Name', 
                 'Client Status', 'Account Manager', 'Team Manager', 'Due Date',
                 'Date Added' ]

    def _records(self, data):
        try:
            records = []
            filts = []
            if self._start:
                filts.append(func.date(UserTask.created_on)>=self._start)
            if self._end:
                filts.append(func.date(UserTask.created_on)<=self._end)

            query = UserTask.query 
            if len(filts) > 0:
                query = query.filter(and_(*filts))
            tasks = query.all()
            for task in tasks:
                client = task.client
                record = {
                    'id': task.id,
                    'desc': task.description,
                    'status': task.status,
                    'type': 'CS Task',
                    'client_id': client.friendly_id if client else '',
                    'client_name': client.full_name if client else '',
                    'client_status': client.disposition.value if client else '',
                    'account_manager': task.owner.full_name,
                    'team_manager': '',
                    'due_date': task.due_date.strftime('%m/%d/%Y'),
                    'inserted_on': task.created_on.strftime('%m/%d/%Y'), 
                }
                records.append(record)

            return records

        except Exception as err:
            app.logger.warning("Task report service {}".format(str(err)))
            return []
