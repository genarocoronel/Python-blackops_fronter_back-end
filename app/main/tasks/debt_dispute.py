from app.main.model.debt import DebtDispute

def on_timer_expiry():
    # active disputes  
    disputes = DebtDispute.query.filter_by(is_active=True).all()
    for dispute in disputes:
        try:
            dispute.on_day_tick()
        except Exception as err:
            continue
    
