from app.main import db
from .docusign import DocuSign
from .models import DocusignTemplate 


# scheduled task
# synchronize template details from Docusign account
def sync_templates():
    try: 
        ds = DocuSign()  
        # authorize the interface
        ds.authorize() 
        templates = ds.fetch_templates()
        for template in templates:
            key = template['id']
            name = template['name']
            # check if present in database
            exists = db.session.query(
                db.session.query(DocusignTemplate).filter_by(ds_key=key).exists()
            ).scalar()

            # if not, add to the database
            if not exists:
                ds_tmpl = DocusignTemplate(name=name, ds_key=key)
                db.session.add(ds_tmpl)
                db.session.commit()
                #print(ds_tmpl.id)
    except Exception as err:
        print("sync_templates task {}".format(str(err)))

# worker task 
# send template for signing
def send_template_for_signing(client_id, template_id, template_params):
    try:
        client = Client.query.filter_by(id=client_id).first()
        if client is None:
            raise ValueError('Client not found')

        tmpl = DocusignTemplate.query.filter_by(id=template_id).first() 
        if tmpl is None:
            raise ValueError('Template not found')

        ds = DocuSign()
        ds.authorize()
        env_id = ds.request_signature(tmpl.ds_key, 
                                      client.first_name, 
                                      client.email,
                                      template_params=template_params)        
        # create a database entry
        signature = DocusignSignature(envelope_id=env_id,
                                      status=SignatureStatus.SENT,
                                      client_id=client_id,
                                      template_id=template_id)
        db.session.add(signature)
        db.session.commit()

    except Exception as err:
        print("send template for signing task {}".format(str(err)))


# task
# update signature status
def update_signature_status():
    try:
        ds = DocuSign()
        ds.authorize()

        signatures = DocusignSignature.query.filter_by(status=SignatureStatus.SENT).all()
        for signature in signatures:
            status = ds.envelope_status(signature.envelope_id)    

            if status.lower() != SignatureStatus.SENT.name.lower():
                # update database
                signature.status = _to_status(status)
                db.session.commit()


    except Exception as err:
        print("Update signature status {}".format(str(err)))


def _to_status(status_txt):
    status_txt = status_txt.lower()
    result = SignatureStatus.CREATED 
    if 'sent' in  status_txt:
        result = SignatureStatus.SENT
    elif 'signed' in status_txt:
       result = SignatureStatus.SIGNED
    elif 'created' in status_txt:
       result = SignatureStatus.Created
    elif 'delivered' in status_txt
       result = SignatureStatus.DELIVERED
    elif 'voided' in status_txt
       result = SignatureStatus.VOIDED

    return result
