from app.main.util.dto import LeadDto
from flask_restplus import marshal
from app.main.model.debt_payment import DebtEftStatus

# Client serializer
class ClientFilterSerializer(object):
    @classmethod
    def serialize(cls, obj):
        client_list = [] 
        record_set = obj['data']         
        for record in record_set:         
            client = marshal(record.Client, LeadDto.lead) 
            contract = record.active_contract
            active_contract = {}
            if contract:
                balance = round((contract.term * contract.monthly_fee) - contract.total_paid, 2)
                active_contract = {
                  'term': contract.term,
                  'total_debt': contract.total_debt,
                  'monthly_fee': contract.monthly_fee,
                  "total_paid": contract.total_paid,
                  "num_term_paid": contract.num_inst_completed,
                  "balance": balance,
                  'payment_1st_date': contract.payment_start_date.strftime("%m-%d-%Y"),
                  'payment_2nd_date': contract.payment_recurring_begin_date.strftime("%m-%d-%Y"),
                  'next_draft_date': '',
                }
                # next schedule
                for schedule in contract.payment_schedule:
                    if schedule.status == DebtEftStatus.FUTURE.name:
                       active_contract['next_draft_date'] = schedule.due_date.strftime("%m-%d-%Y") 
                       break
            client['payment_contract'] = active_contract
            client_list.append(client)
        obj['data'] = client_list


        return obj

class LeadFilterSerializer(ClientFilterSerializer):
    pass
