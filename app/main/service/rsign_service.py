from ..model.docsign import DocusignSession, DocusignTemplate, SessionState, SignatureStatus
from ..model.client import Client
from app.main import db
from sqlalchemy import desc

from flask import current_app as app

def create_session(data):
    if 'client_id' not in data:
        raise ValueError("Missing arguments")
    if 'document' not in data:
        raise ValueError("Missing arguments")

    client_id = data['client_id']    
    doc = data['document']         
    print(client_id)
    # fetch the client
    client = Client.query.filter_by(public_id=client_id).first()
    if client is None:
        raise ValueError("Client not found, client id is Invalid")

    # check if session is already in Progress
    sessions = DocusignSession.query.filter_by(client_id=client.id, state=SessionState.PROGRESS).all()
    if len(sessions) > 0:
        raise ValueError("Create session is not allowed when session is already in progress")

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
    if ds_template is None:
        raise ValueError("Templates are not synchronized, run sync routine !!")    

    session = DocusignSession(template_id=ds_template.id,
                              client_id=client.id,
                              cosign_required=co_sign)
    db.session.add(session)
    db.session.commit()
    app.queue.enqueue('app.main.tasks.docusign.{}'.format(func), session.id)

    return session.id

def fetch_session_status(key):
    try:
        result = {}

        session = DocusignSession.query.filter_by(id=int(key)).first() 
        if session is None:
            raise ValueError("Session not found.")

        if session.state == SessionState.COMPLETED:
            result['status'] = "Completed"
        else:
            signature = session.signature
            if signature is None:
                result['status'] = 'Failed' 
                result['reason'] = 'Internal Server Error'
                return result
 
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
        raise ValueError("Internal Server Error")


def fetch_client_status(client_id):
    try:
        result = {}
        client = Client.query.filter_by(public_id=client_id).first()

        # fetch the latest session
        session = DocusignSession.query.filter_by(client_id=client.id).order_by(desc(DocusignSession.created_date)).first()
        if session is None:
            raise ValueError("rsign session not found") 

        if session.state == SessionState.COMPLETED:
            result['status'] = "Completed"
        else:
            signature = session.signature
            if signature is None:
                result['status'] = 'Failed'
                result['reason'] = 'Internal Server Error'
            else:
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

        result['created_at'] = session.created_date.strftime('%m/%d/%Y')
        result['document'] = session.session_type.value

        return result

    except Exception as err:
        app.logger.warning('fetch client status, {}'.format(str(err)))
        raise ValueError("Internal Server Error") 
