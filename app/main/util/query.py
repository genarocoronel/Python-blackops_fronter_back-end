import datetime

from sqlalchemy import orm, and_

from app.main import db


def build_query_from_dates(query: orm.Query, from_date: datetime.datetime, to_date: datetime.datetime, model: db.Model, *fields):
    """
    build upon an existing query object based on date time frames for the given fields provided

    :param query: existing query object
    :param from_date: optional, datetime in the past
    :param to_date: optional, datetime following from_date
    :param model: database model containing fields to be filtered
    :param fields: datetime fields to be filtered
    :return: query object
    """
    assert query, 'existing query object is required'

    for field in fields or ():
        column = getattr(model, field, None)
        assert column, f'column \'{field}\' is invalid'

        if from_date is not None and to_date is not None:
            query = query.filter(and_(column >= from_date, column <= to_date))
        elif from_date is not None:
            query = query.filter(column >= from_date)
        elif to_date is not None:
            query = query.filter(column <= to_date)
        else:
            raise ValueError("Not a valid datetime filter query")

    return query
