from ..model.docsign import DocusignSession, DocusignTemplate, SessionState
from app.main import db

from flask import current_app as app

def create_session(data):
    if 'client_id' not in data:
        raise ValueError("Missing arguments")
    if 'document' not in data:
        raise ValueError("Missing arguments")

    try:
        client_id = data['client_id']    
        print(client_id)
        # obtain co-sign information
        # testing
        co_sign  = data['co_sign']
        doc = data['document']         

        if "NewContract" in doc:
            tmpl_name = 'EliteDMS_Contract_ 1Signed'
            if co_sign is True:
                tmpl_name = 'EliteDMS_Contract_ 2Signed'
            func = 'send_contract_for_signature' 
        elif "ModifyDebts" in doc:
            tmpl_name = 'Modify Debts'
            if co_sign is True:
                tmpl_name = 'Modify Debts 2Signer'
            func = 'send_modify_debts_for_signature'            

        ds_template = DocusignTemplate.query.filter_by(name=tmpl_name).first()
        session = DocusignSession(template_id=ds_template.id,
                                  client_id=client_id,
                                  cosign_required=co_sign)
        db.session.add(session)
        db.session.commit()
        app.queue.enqueue('app.main.tasks.docusign.{}'.format(func), session.id)

        return session.id

    except Exception as err:
        print(str(err))
        raise ValueError("Internal Error") 


def fetch_session_status(key):
    try:
        session = DocusignSession.query.filter_by(id=int(key)).first() 
        # check the status
        if session.state == SessionState.PROGRESS:
            status = "Progress"
            reason = "In Progress"
        elif session.state == SessionState.FAILED:
            status = "Failed"
            reason = "Failure reason"
        elif session.state == SessionState.COMPLETED:
            status = "Completed"
            reason = "Signtaure Completed"
            
        return { 'status' : status, 'reason': reason }

    except Exception as err:
        raise ValueError("Internal Error")
