from marshmallow import Schema
from marshmallow.fields import Integer
from marshmallow.fields import String

class SMTPConfSchema(Schema):
    host = String()
    port = Integer()


class OracleConfSchema(Schema):
    oracle_lib_dir = String()
    drivername = String()
    host = String()
    port = Integer()
    username = String()
    password = String()
    database = String()
    query = String()
