import enum

class CustomerType(enum.Enum):
    CANDIDATE = 'candidate'
    LEAD = "lead"
    CLIENT = "client"
    COCLIENT = "coclient"