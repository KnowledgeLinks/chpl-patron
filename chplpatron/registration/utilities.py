"""
Utility Methods and wrappers for registration app
"""
__author__ = "Jeremy Nelson, Mike Stabile"

from enum import Enum
from flask import make_response, request, current_app
from datetime import timedelta
from functools import update_wrapper
from chplpatron.sierra import PatronFlds

basestring = (str, bytes)


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """
    Wrapper for handling cross domain requests

    :param origin:
    :param methods:
    :param headers:
    :param max_age:
    :param attach_to_all:
    :param automatic_options:
    :return:
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


class FldSpec:
    """
    Stores associative data for fields
    """
    __slots__ = ['name', 'frm', 'api', 'db', 'concat']

    def __init__(self, name, frm, api=None, db=None, concat=None):
        self.name = name
        self.frm = frm
        self.db = db
        self.api = api
        self.concat = concat


ADDRESS_CONCAT = {"separator": ", ",
                  "fields": ["street", "city", "state", "postal_code"]}
NAMES_CONCAT = {"separator": ", ",
                "fields": ["last_name", "first_name"]}


class FldAssoc(Enum):
    first_name = FldSpec("first_name",
                         "g587-firstname",
                         PatronFlds.names,
                         NAMES_CONCAT)
    last_name = FldSpec("last_name",
                        "g587-lastname",
                        PatronFlds.names,
                        NAMES_CONCAT)
    birthday = FldSpec("birthday", "g587-birthday", PatronFlds.birthDate)
    street = FldSpec("street",
                     "g587-address",
                     PatronFlds.addresses,
                     ADDRESS_CONCAT)
    city = FldSpec("city",
                   "g587-city",
                   PatronFlds.addresses,
                   ADDRESS_CONCAT)
    state = FldSpec("state",
                    "g587-state",
                    PatronFlds.addresses,
                    ADDRESS_CONCAT)
    postal_code = FldSpec("postal_code",
                          "g587-zipcode",
                          PatronFlds.addresses,
                          ADDRESS_CONCAT)
    phone = FldSpec("phone",
                    "g587-telephone",
                    PatronFlds.phones)


def convert(data, input, output):
    if input == "form":
        return form_convert(data, output)
    elif input == "db":
        return db_convert(data, output)
    elif input == "api":
        return api_convert(data, output)


def form_convert(data, output):
    pass


def db_convert(data, output):
    pass


def api_convert(data, output):
    pass
