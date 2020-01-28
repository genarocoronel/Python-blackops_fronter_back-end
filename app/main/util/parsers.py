import werkzeug
from flask_restplus import reqparse
from datetime import datetime

file_upload = reqparse.RequestParser()
file_upload.add_argument('csv_file',
                         type=werkzeug.datastructures.FileStorage,
                         location='files',
                         required=True,
                         help='CSV file')


# utility api to parse generic filter arguments
# @return dictionary of structured filter set
def filter_request_parse(request):
    result = {}

    limit = request.args.get('_limit', None)
    order = request.args.get('_order', None)
    sort  = request.args.get('_sort', None) 
    pagenum = request.args.get('_page_number', None)
    # string filter fields
    str_fields = []
    search = None
    fields = request.args.get('_q', None)
    if fields is not None:
        str_fields = [x.strip() for x in fields.split(',')]
    if len(str_fields) > 0:
        search = request.args.get('_search', None)
    # date filters
    dt_fields = []
    from_date = None
    to_date   = None
    fields = request.args.get('_dt', None)
    if fields is not None:
        dt_fields = [x.strip() for x in fields.split(',')]
    if len(dt_fields) > 0:
        from_date = request.args.get('_from', None)
        to_date = request.args.get('_to', None)

    # numeric fields
    numeric_fields = None
    fields = request.args.get('_iq', None)
    if fields is not None:
        numeric_fields = [x.strip() for x in fields.split(',')]

    if limit is not None:
        result['limit'] = int(limit)
    if sort is not None:
        result['sort_col'] = sort
    if order is not None:
        result['order'] = order
    if pagenum is not None:
        result['pageno'] = int(pagenum)
    if len(str_fields) > 0:
        result['search_fields'] = str_fields
        if search is not None:
            result['search_val'] = search
    if len(dt_fields) > 0:
        result['dt_fields'] = dt_fields
        if from_date is not None and from_date.strip() != "":
            result['from_date'] = datetime.strptime(from_date, "%Y-%m-%d")
        if to_date is not None and to_date.strip() != "":
            result['to_date'] = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23,minute=59)
    if numeric_fields is not None:
        result['numeric_fields'] = numeric_fields

    return result
