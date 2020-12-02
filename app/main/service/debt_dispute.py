from app.main import db
from app.main.model.debt import DebtDispute, DebtDisputeStatus
from app.main.model.credit_report_account import CreditReportData
from app.main.core.errors import BadParamsError
from app.main.tasks import mailer
from sqlalchemy import desc
from datetime import datetime
from flask import current_app as app


class DebtDisputeService(object):

    @classmethod
    def fetch_all(cls, client, debt_id):
        debt = CreditReportData.query.filter_by(public_id=debt_id).first()
        disputes = DebtDispute.query.filter_by(client_id=client.id, 
                                              debt_id=debt.id).all()
        return disputes

    @classmethod
    def process_collection_letter(cls, 
                                  client, # Client, 
                                  debt,   # CreditReportData, 
                                  doc):   # Docproc
        # client not valid
        if not client:
            raise BadParamsError('Client parameter is not present') 
        # debt not valid
        if not debt:
            raise BadParamsError('Debt parameter is not present')
        # debt collector
        if not debt.collector_id:
            raise BadParamsError('Debt Collector is not present in Debt record')
        
        # retreive active dispute item 
        debt_dispute = DebtDispute.query.filter_by(client_id=client.id,
                                                   debt_id=debt.id,
                                                   is_active=True).first()
        # create a debt dispute
        if not debt_dispute:
            now = datetime.utcnow()
            # determine the sold package or not
            task_func = 'send_initial_dispute_mail'
            status = DebtDisputeStatus.P1_SEND.name

            old_dispute = DebtDispute.query.filter_by(client_id=client.id,
                                                      debt_id=debt.id,
                                                      is_active=False).order_by(desc(DebtDispute.created_date)).first()

            if old_dispute and old_dispute.collector_id != debt.collector_id:
                 task_func = 'send_sold_package_mail'
                 status = DebtDisputeStatus.SOLD_PACKAGE_SEND.name
            
            debt_dispute = DebtDispute(client_id=client.id,
                                       debt_id=debt.id,
                                       status=status,
                                       is_active=True,
                                       p1_date=now,
                                       collector_id=debt.collector_id,
                                       collector_ref_no=debt.collector_ref_no,
                                       created_date=now,
                                       modified_date=now)
            db.session.add(debt_dispute)
            db.session.commit()
            # send P1/Sold package 
            app.queue.enqueue('app.main.tasks.mailer.{}'.format(task_func), 
                              client.id, 
                              debt.id,
                              debt_dispute.id,
                              failure_ttl=300)


        else:
            # check if debt is sold to another collector or not
            # send sold package
            if debt_dispute.collector_id != debt.collector_id:
                debt_dispute.is_active = False

                task_func = 'send_sold_package_mail'
                status = DebtDisputeStatus.SOLD_PACKAGE_SEND.name

                # create new dispute
                new_dispute = DebtDispute(client_id=client.id,
                                          debt_id=debt.id,
                                          status=status,
                                          is_active=True,
                                          p1_date=now,
                                          collector_id=debt.collector_id,
                                          collector_ref_no=debt.collector_ref_no,
                                          created_date=now,
                                          modified_date=now)

                db.session.add(new_dispute)
                db.session.commit()

                app.queue.enqueue('app.main.tasks.mailer.{}'.format(task_func),
                                  client.id,
                                  debt.id,
                                  new_dispute.id,
                                  failure_ttl=300) 
            else:
                # collector response
                cls.on_collector_response(debt_dispute)     

    @classmethod
    def on_collector_response(cls, disp):
        now = datetime.utcnow()
        if disp.status == DebtDisputeStatus.P1_SEND.name or\
           disp.status == DebtDisputeStatus.SOLD_PACKAGE_SEND.name or\
           disp.status == DebtDisputeStatus.P2_SEND.name or\
           disp.status == DebtDisputeStatus.FULLY_DISPUTED_NON_RESPONSE_EXPIRED.name or\
           disp.status == DebtDisputeStatus.FULLY_DISPUTED_NOIR_EXPIRED:
            disp.noir_date = now
            disp.status = DebtDisputeStatus.NOIR_SEND.name
            disp.debt.last_debt_status = DebtDisputeStatus.NOIR_SEND.value
            db.session.commit()
            # send
            mailer.send_noir_notice(disp.client_id,
                                    disp.debt_id,
                                    disp.id)
        elif disp.status == DebtDisputeStatus.NOIR_SEND.name:
            disp.noir2_date = now
            disp.status = DebtDisputeStatus.NOIR2_SEND.name
            disp.debt.last_debt_status = DebtDisputeStatus.NOIR2_SEND.value
            db.session.commit()
            # send 
            mailer.send_noir_2_notice(disp.client_id,
                                      disp.debt_id,
                                      disp.id)
        elif disp.status == DebtDisputeStatus.NOIR2_SEND.name:
            disp.noir_fdcpa_date = now
            disp.status = DebtDisputeStatus.NOIR_FDCPA_SEND.name
            disp.debt.last_debt_status = DebtDisputeStatus.FDCPA_SEND.value
            db.session.commit()
            # send
            mailer.send_noir_fdcpa_notice(disp.client_id,
                                          disp.debt_id,
                                          disp.id)
        elif disp.status == DebtDisputeStatus.NOIR_FDCPA_SEND.name:
            disp.status = DebtDisputeStatus.NOIR_FDCPA_WAIT.name
            db.session.commit()

    @classmethod
    def on_day_tick(cls, disp):
        now = datetime.utcnow()
        if disp.status == DebtDisputeStatus.P1_SEND.name or\
           disp.status == DebtDisputeStatus.SOLD_PACKAGE_SEND.name:
            diff = (now - disp.p1_date)
            days_expired = diff.days
            # check
            if days_expired > 30:
                disp.p2_date = now
                disp.status = DebtDisputeStatus.P2_SEND.name
                disp.debt.last_debt_status = DebtDisputeStatus.P2_SEND.value
                db.session.commit()
                # Send Non response notice
                mailer.send_non_response_notice(disp.client_id,
                                                disp.debt_id,
                                                disp.p1_date,
                                                disp.id)
                # Send non response ack
                mailer.send_non_response_ack(disp.client_id,
                                             disp.debt_id)

        elif disp.status == DebtDisputeStatus.P2_SEND.name:
            diff = (now - disp.p2_date)
            days_expired = diff.days
            # more than 20 days
            if days_expired > 20:
                # Send fully disputed ack to client
                mailer.send_fully_dispute_ack(disp.client_id,
                                              disp.debt_id)
                disp.fd_non_response_expired_date = now
                disp.status = DebtDisputeStatus.FULLY_DISPUTED_NON_RESPONSE_EXPIRED.name
                disp.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_NON_RESPONSE_EXPIRED.value

                log_title = 'No Non-Response Response Received'
                msg = ''
                status = DebtDisputeStatus.FULLY_DISPUTED_NON_RESPONSE_EXPIRED.value 
                log = DebtDisputeLog(created_on=now,
                                     title=log_title,
                                     message=msg,
                                     dispute_id=disp.id,
                                     status=status)
                db.session.add(log)
                db.session.commit()

        elif disp.status == DebtDisputeStatus.NOIR_SEND.name:
            diff = (now - disp.noir_date)
            days_expired = diff.days
            if days_expired > 10:
                mailer.send_fully_dispute_ack(disp.client_id,
                                              disp.debt_id)
                disp.fd_noir_expired_date = now
                disp.status = DebtDisputeStatus.FULLY_DISPUTED_NOIR_EXPIRED.name
                disp.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_NOIR_EXPIRED.value
                log_title = 'No NOIR Response Received'
                msg = ''
                status = DebtDisputeStatus.FULLY_DISPUTED_NOIR_EXPIRED.value
                log = DebtDisputeLog(created_on=now,
                                     title=log_title,
                                     message=msg,
                                     dispute_id=disp.id,
                                     status=status)
                db.session.add(log)
                db.session.commit()
        elif disp.status == DebtDisputeStatus.NOIR2_SEND.name:
            diff = (now - disp.noir2_date)
            days_expired = diff.days
            if days_expired > 10:
                mailer.send_fully_dispute_ack(disp.client_id,
                                              disp.debt_id)
                disp.fully_disputed_date = now
                disp.status = DebtDisputeStatus.FULLY_DISPUTED_EXPIRED.name
                disp.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_NOIR2_EXPIRED.value
                log_title = 'No NOIR2 Response Received'
                msg = ''
                status = DebtDisputeStatus.FULLY_DISPUTED_NOIR2_EXPIRED.value
                log = DebtDisputeLog(created_on=now,
                                     title=log_title,
                                     message=msg,
                                     dispute_id=disp.id,
                                     status=status)

                db.session.add(log)
                db.session.commit()
        elif disp.status == DebtDisputeStatus.NOIR_FDCPA_SEND.name:
            diff = (now - disp.noir_fdcpa_date)
            days_expired = diff.days
            if days_expired > 10:
                mailer.send_fully_dispute_ack(disp.client_id,
                                              disp.debt_id)
                disp.fully_disputed_date = now
                disp.status = DebtDisputeStatus.FULLY_DISPUTED_EXPIRED.name
                disp.debt.last_debt_status = DebtDisputeStatus.FULLY_DISPUTED_FDCPA_EXPIRED.value
                log_title = 'No NOIR2 Response Received'
                msg = ''
                status = DebtDisputeStatus.FULLY_DISPUTED_FDCPA_EXPIRED.value
                log = DebtDisputeLog(created_on=now,
                                     title=log_title,
                                     message=msg,
                                     dispute_id=disp.id,
                                     status=status)
                db.session.add(log)
                db.session.commit()
        elif disp.status == DebtDisputeStatus.NOIR_FDCPA_WAIT.name:
            diff = (now - disp.fully_disputed_date)
            days_expired = diff.days
            if days_expired > 90:
                disp.is_active = False

                log_title = 'Auto Disputed'
                msg = ''
                status = DebtDisputeStatus.FULLY_DISPUTED_FDCPA_EXPIRED.value
                log = DebtDisputeLog(created_on=now,
                                     title=log_title,
                                     message=msg,
                                     dispute_id=disp.id,
                                     status=status)
                db.session.add(log)
                db.session.commit()
