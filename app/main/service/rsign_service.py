from ..model.docsign import DocusignSession, DocusignTemplate, SessionState, SignatureStatus
from ..model.client import Client
from app.main import db

from flask import current_app as app

def create_session(data):
    if 'client_id' not in data:
        raise ValueError("Missing arguments")
    if 'document' not in data:
        raise ValueError("Missing arguments")

    try:
        client_id = data['client_id']    
        doc = data['document']         
        print(client_id)
        # fetch the client
        client = Client.query.filter_by(id=int(client_id)).first()
        # obtain co-sign information
        co_sign = False
        if client.client_id is not None:
            co_sign = True

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
        result = {}

        session = DocusignSession.query.filter_by(id=int(key)).first() 
        if session is None:
            raise ValueError("Session not found.")

        if session.state == SessionState.COMPLETED:
            result['status'] = "Completed"
        else:
            signatures = session.signatures
            for signature in signatures:
                status = signature.status
                if session.state == SessionState.PROGRESS:
                    result['status'] = "Progress"
                    if (status == SignatureStatus.COMPLETED):
                        result['status'] = 'Completed'
                    elif (status == SignatureStatus.DELIVERED):
                        result['status'] = 'Delivered'
                    elif (status == SignatureStatus.SIGNED):
                        result['status'] = 'Signed'
                elif session.state == SessionState.FAILED:
                    result['status'] = "Failed"
                    if (status == SignatureStatus.DECLINED):
                        result['status'] = 'Declined'
                    elif (status == SignatureStatus.VOIDED):
                        result['status'] = 'Voided'
            
        return result

    except Exception as err:
        raise ValueError("Internal Error")
