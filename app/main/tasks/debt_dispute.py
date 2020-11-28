from app.main.model.debt import DebtDispute
from app.main.service.debt_dispute import DebtDisputeService

def on_timer_expiry():
    # active disputes  
    disputes = DebtDispute.query.filter_by(is_active=True).all()
    for dispute in disputes:
        try:
            DebtDisputeService.on_day_tick(dispute)
        except Exception as err:
            continue
    
