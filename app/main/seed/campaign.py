from app.main.model.campaign import PinnaclePhoneNumber
from app.main import db

phone_numbers = [
    '18777081208',
    '18777081210',
    '18777081340',
    '18777081320',
    '18777081220',
    '18777081421',
    '18777081387',
    '18777081361',
    '18777081493',
    '18777081236',
    '18777081428',
    '18777080498',
    '18777080488',
    '18777081356',     
    '18777081557',     
    '17603491710',     
    '17603491709',     
    '18777081347',     
]

def seed_pinnacle_phone_numbers():
    for number in phone_numbers:
        ppn = PinnaclePhoneNumber.query.filter_by(number=number).first()
        if not ppn:
            ppn = PinnaclePhoneNumber(number=number)
            db.session.add(ppn)
        db.session.commit()
  
