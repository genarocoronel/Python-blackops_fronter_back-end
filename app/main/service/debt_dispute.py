from app.main import db
from app.main.model.debt import DebtDispute, DebtDisputeStatus
from datetime import datetime
from flask import current_app as app


class DebtDisputeService(object):


    @classsmethod
    def process_collection_letter(cls, client, debt):
        # retreive active dispute item 
        debt_dispute = DebtDispute.query.filter_by(client_id=client.id,
                                                   debt_id=debt.id,
                                                   is_active=True).first()
        # create a debt dispute
        if not debt_dispute:
            today = datetime.utcnow()
            # determine the sold package or not
            task_func = 'send_initial_dispute_mail'
            status = DebtDisputeStatus.P1_SEND.name
            
            # send P1 
            app.queue.enqueue('app.main.tasks.mailer.{}'.format(task_func), 
                              client.id, 
                              debt.id)

            debt_dispute = DebtDispute(client_id=client.id,
                                       debt_id=debt.id,
                                       status=status,
                                       is_active=True,
                                       p1_date=today,)
            db.session.add(debt_dispute)
            db.session.commit()
        else:
            # collector response
            debt_dispute.on_collector_response()     
