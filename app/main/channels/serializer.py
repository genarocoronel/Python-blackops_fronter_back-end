from flask_restplus import marshal
from functools import wraps


## serialization utility
def serialize(func_to_decorate):
    @wraps(func_to_decorate)
    def decorated(cls, user_id, data):
        params = marshal(data, cls.serializer_class)
        return func_to_decorate(cls, user_id, params)
    return decorated

def bcast_serialize(func_to_decorate):
    @wraps(func_to_decorate)
    def decorated(cls, data):
        params = marshal(data, cls.serializer_class)
        return func_to_decorate(cls, params)
    return decorated

