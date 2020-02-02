import enum

from .. import db


class AddressType(enum.Enum):
    CURRENT = 'CURRENT'
    PAST = 'PAST'


class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    address1 = db.Column(db.String(100), nullable=False)
    address2 = db.Column(db.String(100), nullable=True)
    _zip_code = db.Column('zip_code', db.String(10), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(20), nullable=False)
    from_date = db.Column(db.Date())
    to_date = db.Column(db.Date())
    type = db.Column(db.Enum(AddressType), nullable=False)

    def _zip_code_parts(self):
        return self._zip_code.strip('-').split('-')

    @property
    def zip_code(self):
        zip_parts = self._zip_code_parts()
        if len(zip_parts) > 1:
            return self._zip_code
        else:
            return zip_parts[0]

    @zip_code.setter
    def zip_code(self, zip_code):
        zip = zip_code.strip('-').split('-')
        if len(zip) > 1:
            self._zip_code = zip
        else:
            self._zip_code = zip[0]

    @property
    def zip5(self):
        return self._zip_code_parts()[0]

    @property
    def zip4(self):
        zip_parts = self._zip_code_parts()
        if len(zip_parts) > 1:
            return zip_parts[1]
        return ''
