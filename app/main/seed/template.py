from app.main.model.template import *


def seed_templates():
    records = [
      # Send five days prior to the payment date of the client preferably around 12pm
      { 'title': 'Payment Reminder', 'action': 'PAYMENT_REMINDER', 'path': 'pending_payment_notice.html', 'editable': True, 'desc': 'Send five days prior to the payment date of the client preferably around 12pm', 'subject': 'Your upcoming payment to Elite DMS'},
      # Send when the user changes the status to "Complete" after any phone appointment in the CS schedule
      { 'title': 'Spanish General Call', 'action': 'SPANISH_GENERAL_CALL', 'path': 'spanish_general_call.html', 'editable': True, 'desc': 'Send when the user changes the status to Complete after any phone appointment in the CS schedule', 'subject': 'RESUMEN DE SU LLAMADA CON ELITE DMS'},
      # Send to Client when status is changed to "Request Cancellation" action.
      { 'title': 'Cancellation Request (Email)', 'action': 'CANCELLATION_REQUEST', 'path': 'cancellation_request.html', 'editable': True, 'desc': 'Send to Client when status is changed to Request Cancellation action.', 'medium':'EMAIL_SMS', 'subject': 'A request to cancel the Elite DMS program has been received'},
      # Send when EPPS returns status as unsuccessful (not sure what the exact EPPS words are) on any payment.
      { 'title': 'NSF Draft Issue', 'action': 'NSF_DRAFT_ISSUE', 'path': 'nsf_draft_issue.html', 'editable': True, 'desc': 'Send when EPPS returns status as unsuccessful on any payment', 'subject': 'Payment Issue-Please contact your account manager'},
      # Send one hour prior to the clients next scheduled appointment in the CRM.  Ensure the CRM corrects properly for timezones
      { 'title': '1 Hour Appointment Reminder (Email)', 'action': 'HOUR1_APPOINTMENT_REMINDER', 'path': 'h1_appointment_reminder.html', 'editable': True, 'desc': 'Send one hour prior to the clients next scheduled appointment in the CRM.', 'subject': 'Appointment reminder in 1 hour for Elite DMS'},
      # Send when a service user or service manager successfully completes the change payment date process on the EDMS tab
      { 'title': 'Change of Payment Date (Email)', 'action': 'CHANGE_PAYMENT_DATE', 'path': 'change_payment_date.html', 'editable': True, 'date': 'Send when a service user or service manager successfully completes the change payment date.', 'medium':'EMAIL_SMS', 'subject': 'Payment Date Change confirmation'},
      # Send 1 day prior to the client's next scheduled appointment…preferably in the afternoon
      { 'title': '1 Day Appointment Reminder (Email)', 'action': 'DAY1_APPOINTMENT_REMINDER', 'path': 'd1_appointment_reminder.html', 'editable': True, 'desc': 'Send 1 day prior to the clients next scheduled appointment…preferably in the afternoon', 'medium': 'EMAIL_SMS', 'subject': 'Appointment reminder tomorrow for Elite DMS'},
      # Send when the user changes the status to "Complete" after any phone appointment in the CS schedule
      { 'title': 'General', 'action': 'GENERAL_CALL_EDMS', 'path': 'general_call.html', 'editable': True, 'desc': 'Send when the user changes the status to "Complete" after any phone appointment in the CS schedule', 'subject': 'Summary of todays call with Elite DMS'},
      # When specific Debt Status Changes to NOIR Sent (Debt status is on debt creditor tab)
      { 'title': 'NOIR Auto (Email)', 'action': 'NOIR_SENT_ACK', 'path': 'noir_sent_ack.html', 'editable': True, 'desc': 'When specific Debt Status Changes to NOIR Sent (Debt status is on debt creditor tab)', 'subject': 'Update on one of your accounts'},
      # Send when 15 day call is marked as "Complete" in the clients CS Schedule
      { 'title': '15 Day Call', 'action': 'DAY15_CALL_ACK', 'path': 'd15_call_ack.html', 'editable': True, 'desc': 'Send when 15 day call is marked as "Complete" in the clients CS Schedule', 'subject': 'Summary of todays call with Elite DMS'},
      # Spanish Client only. Send when 15 day call is marked as "Complete" in the clients CS Schedule
      { 'title': 'Spanish Intro', 'action': 'SPANISH_INTRO', 'path': 'spanish_intro.html', 'editable': True, 'desc': 'Spanish Client only. Send when 15 day call is marked as "Complete" in the clients CS Schedule', 'subject': 'Información de contacto del gerente de cuenta Elite DMS'},
      # Send when Changing status to "NOIR Sent", send through fax if there IS a FAX number in the 3rd party debt collector fax number box else POST.
      { 'title': 'NOIR EDMS Notice', 'action': 'NOIR_NOTICE', 'path': 'noir_common.html', 'medium': 'FAX', 'editable': True, 'desc': 'Send when Changing status to NOIR Sent, send through fax if there IS a FAX number in the 3rd party debt collector fax number box else POST.'},
      # Send fax when changing status to "Non-Response Sent" automatically after 50 days from the date the P1 dispute letter is sent and 
      # there IS a fax number in the 3rd party debt collector "fax number" box
      { 'title': 'Non Response EDMS Notice', 'action': 'NON_RESPONSE_NOTICE', 'path': 'non_response_notice.html', 'medium': 'FAX', 'editable': True, 'desc': 'Send when changing status to Non-Response Sent automatically after 50 days from the date the P1 dispute letter is sent'},
      # Send fax when Changing status to NOIR FDCPA Only, and there IS a FAX number in the 3rd party debt collector fax number box
      { 'title': 'NOIR FDCPA EDMS', 'action': 'NOIR_FDCPA_NOTICE', 'path': 'fdcpa_insufficient_response.html', 'medium': 'FAX', 'editable': True, 'desc': 'Send when Changing status to NOIR FDCPA Only, and there IS a FAX number in the 3rd party debt collector fax number box.'},
      # Send when service user "Completes" the "Introduction Call" on the CS Schedule (EDMS)
      { 'title': 'Intro Call', 'action': 'INTRO_CALL', 'path': 'intro_call.html', 'editable': True, 'desc': 'Send when service user Completes the Introduction Call on the CS Schedule', 'subject': 'Elite DMS account manager contact information'},
      # Initiated by Sales or Service user to send email.  No contact will be an option on the dropdown menu when user clicks 
      # on the mail icon next to other comm icons under the 
      { 'title': 'No Contact', 'action': 'NO_CONTACT_CANCELLATION', 'path': 'no_contact_cancel_notice.html', 'editable': True, 'desc': 'Initiated by Sales or Service user to send email. No contact will be an option on the dropdown menu when user clicks on the mail icon next to other comm icons under the client name on the main tab.','trigger_mode': 'MANUAL', 'subject': 'Action Requested-We havent been able to reach you'},
      # Initiated by Sales or Service user to send email.  Refund will be an option on the dropdown menu 
      # when user clicks on the mail icon next to other comm icons under the client 
      { 'title': 'Refund', 'action': 'REFUND_ACK', 'path': 'refund_ack.html', 'editable': True, 'desc': 'Initiated by Sales or Service user to send email. Refund will be an option on the dropdown menu, when user clicks on the mail icon next to other comm icons under the client', 'trigger_mode': 'MANUAL', 'subject': 'Your refund is being processed by Elite DMS'},
      # Initiated by Sales or Service user to send email.  A blank template will be an option on the dropdown menu 
      # when user clicks on the mail icon next to other comm icons under 
      { 'title': 'Blank Template', 'action': 'BLANK_TEMPLATE', 'path': 'blank_template.html', 'editable': True, 'desc': 'Initiated by Sales or Service user to send email.A blank template will be an option on the dropdown menu when user clicks on the mail icon next to other comm icons under the client name on the main tab.', 'trigger_mode': 'MANUAL'},
      # Email sent to client when Service user changes the Debt Status to "Initial Dispute Sent" on a document type 
      # of "collection letter" when sending the P1 dispute letter 
      { 'title': 'Initial Dispute Sent Notice (Email)', 'action': 'INITIAL_DISPUTE_SENT_ACK', 'path': 'initial_dispute_sent_ack.html', 'editable': True, 'desc': 'Email sent to client when Service user changes the Debt Status to Initial Dispute Sent on a document type of collection letter when sending the P1 dispute letter.', 'subject': 'Dispute Process initiated on one of your accounts'},
      # When Service user or doc processor changes Debt Status to: NOIR 2 Sent, NOIR FDCPA Sent, Sold Package Sent 
      { 'title': 'Other Dispute Sent Notice (Email)', 'action': 'OTHER_DISPUTE_SENT_ACK', 'path': 'other_dispute_sent_ack.html', 'editable': True, 'desc': 'When Service user or doc processor changes Debt Status to: NOIR 2 Sent, NOIR FDCPA Sent, Sold Package Sent', 'subject': 'Dispute process update on one of your accounts'},
      # When Service user or doc processor changes Debt Status to any status that has "Fully Disputed" in it (Full disputed-non response expired, 
      #  Full disputed: NOIR 2 expired, Full disputed:NOIR FDCPA Expired, Full Disputed: Manual, Fully disputed)
      { 'title': 'Fully Disputed Notice (Email)', 'action': 'FULLY_DISPUTED_NOTICE', 'path': 'fully_disputed_notice.html', 'editable': True, 'desc': 'When Service user or doc processor changes Debt Status to any status that has Fully Disputed in it (Full disputed-non response expired, Full disputed: NOIR 2 expired, Full disputed:NOIR FDCPA Expired, Full Disputed: Manual, Fully disputed)', 'subject': 'Dispute process final on one of your accounts'},
      # When Service user or doc processor changes Debt Status to "Non-Response Sent"
      { 'title': 'Non Response sent notice (Email)', 'action': 'NON_RESPONSE_SENT_ACK', 'path': 'non_response_sent_ack.html', 'editable': True, 'desc': 'When Service user or doc processor changes Debt Status to Non-Response Sent', 'subject': 'Dispute process update on one of your accounts'},

      # When Service user or doc processor clicks on Green Send CP login button on the main tab. 
      { 'title': 'Client Portal Login EDMS (Email)', 'action': 'CLIENT_PORTAL_LOGIN', 'path': 'client_portal_login.html', 'editable': True, 'desc': 'When Service user or doc processor clicks on Green Send CP login button on the main tab.', 'subject': 'Client Portal Information'},
      { 'title': 'Spanish Welcome Letter', 'action': 'SPANISH_WELCOME_LETTER', 'path': 'edms_brochure_esp.html', 'editable': False, 'desc': 'Spanish Welcome letter', 'subject': 'Paquete de bienvenida del programa Elite DMS', 'attachment': 'edms_brochure_esp.pdf'},
      { 'title': 'Welcome Letter', 'action': 'WELCOME_LETTER', 'path': 'edms_welcome_package.html', 'editable': False, 'desc': 'Welcome letter', 'subject': 'Elite DMS program Welcome Package', 'attachment': 'edms_welcome_package.pdf'},
      { 'title': 'Privacy Policy', 'action': 'PRIVACY_POLICY', 'path': 'privacy_policy.html', 'editable': False, 'desc': 'EliteDMS Private policy', 'subject': 'Elite DMS Privacy Policy', 'attachment': 'privacy_policy.pdf' },
     
      # Send FAX when Changing status to "Initial Dispute Sent"  
      { 'title': 'Initial Dispute Mail', 'action': 'INITIAL_DISPUTE_MAIL', 'path': 'initial_dispute_mail.html', 'editable': True, 'medium': 'FAX', 'desc': 'Send FAX when Changing status to Initial Dispute Sent'},
      # Send fax when changing status to "Sold Package Sent"  and there IS a FAX number in the 3rd party debt collector "fax number" box
      { 'title': 'Sold Package Mail', 'action': 'SOLD_PACKAGE_MAIL', 'path': 'sold_package_mail.html', 'editable': True, 'medium': 'FAX', 'desc': 'Send when changing status to Sold Package Sent.'},

      { 'title': 'Delete Document (Email)', 'action': 'DELETE_DOCMENT_NOTICE', 'path': 'delete_document_notice.html', 'editable': True, 'desc': 'Sends when document is deleted.', 'subject': 'A document has been deleted'},
      { 'title': 'New Document (Email)', 'action': 'NEW_DOCUMENT_NOTICE', 'path': 'new_document_notice.html', 'editable': True, 'desc': 'Sends when new document is added.', 'subject': 'A document has been created'},
      # Send three days after the client enrolls in the program.  Appointment Reminder 3 Day Text Spanish (SMS). EDMS
      { 'title': 'Old EDMS_3 Day Text Spanish(SMS)', 'action': 'DAY3_REMINDER_SPANISH', 'path': 'day3_reminder_spanish.txt', 'medium': 'SMS',  'editable': True, 'desc': 'Send three days after the client enrolls in the program.  Appointment Reminder 3 Day Text Spanish (SMS)'},
      # Send 3 days after the client enrolls in the program preferably around 12-1PM
      { 'title': 'EDMS_3 Day Text (SMS)', 'action': 'DAY3_REMINDER', 'path': 'day3_reminder.txt', 'medium': 'SMS',  'editable': True, 'desc': 'Send 3 days after the client enrolls in the program preferably around 12-1PM'},
    ]

    for record in records:
        tmpl = Template.query.filter_by(action=record['action']).first()
        if tmpl is None:
            medium = 'EMAIL'
            mode = 'AUTO'
            editable = False
            description = ''
            subject = ''
            attachment = None

            action = record['action']
            if action not in TemplateAction.__members__:
                print("Unknown action {}".format(action))
                continue

            if 'medium' in record:
                medium = record['medium']
            if 'trigger_mode' in record:
                mode = record['trigger_mode']
            if 'editable' in record:
                editable = record['editable']
            if 'desc' in record:
                description = record['desc']
            if 'subject' in record:
                subject = record['subject']
            if 'attachment' in record:
                attachment = record['attachment']

            tmpl = Template(action=action,
                            title=record['title'],
                            description=description,
                            subject=subject,
                            fname=record['path'],
                            attachment=attachment,
                            medium=medium,
                            is_editable=editable,
                            trigger_mode=mode)

            db.session.add(tmpl)

        db.session.commit()
