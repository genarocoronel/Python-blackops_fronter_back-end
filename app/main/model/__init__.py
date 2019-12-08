import enum


class Language(enum.Enum):
    ENGLISH = 'english'
    SPANISH = 'spanish'


class EmploymentStatus(enum.Enum):
    EMPLOYED = 'employed'
    RETIRED = 'retired'
    STUDENT = 'student'
    UNEMPLOYED = 'unemployed'


class Frequency(enum.Enum):
    ANNUAL = 'annual'
    MONTHLY = 'monthly'
