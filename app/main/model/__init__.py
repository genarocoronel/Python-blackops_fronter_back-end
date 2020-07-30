import enum
from . import organization
from . import template
from . import ticket
from . import creditor
from . import sales_board
from . import debt

class Language(enum.Enum):
    ENGLISH = 'english'
    SPANISH = 'spanish'


class Frequency(enum.Enum):
    ANNUAL = 'annual'
    MONTHLY = 'monthly'
