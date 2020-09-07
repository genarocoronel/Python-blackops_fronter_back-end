from app.main import db
from app.main.model.debt import DebtDispute, DebtDisputeStatus
from app.main.core.errors import BadParamsError
from sqlalchemy import desc
from datetime import datetime
from flask import current_app as app


class DebtDisputeService(object):

    @classmethod
    def process_collection_letter(cls, client, debt):
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
            
            # send P1 
            app.queue.enqueue('app.main.tasks.mailer.{}'.format(task_func), 
                              client.id, 
                              debt.id,
                              failure_ttl=300)

            debt_dispute = DebtDispute(client_id=client.id,
                                       debt_id=debt.id,
                                       status=status,
                                       is_active=True,
                                       p1_date=now,
                                       collector_id=debt.collector_id,
                                       created_date=now,
                                       modified_date=now)
            db.session.add(debt_dispute)
            db.session.commit()
        else:
            # check if debt is sold to another collector or not
            # send sold package
            if debt_dispute.collector_id != debt.collector_id:
                debt_dispute.is_active = False

                task_func = 'send_sold_package_mail'
                status = DebtDisputeStatus.SOLD_PACKAGE_SEND.name
                app.queue.enqueue('app.main.tasks.mailer.{}'.format(task_func),
                                  client.id,
                                  debt.id,
                                  failure_ttl=300) 

                # create new dispute
                new_dispute = DebtDispute(client_id=client.id,
                                          debt_id=debt.id,
                                          status=status,
                                          is_active=True,
                                          p1_date=now,
                                          collector_id=debt.collector_id,
                                          created_date=now,
                                          modified_date=now)

                db.session.add(new_dispute)
                db.session.commit()
            else:
                # collector response
                debt_dispute.on_collector_response()     
