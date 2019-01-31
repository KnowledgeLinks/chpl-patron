"""
baseutilities.py

Module of helper functions used in the RDF Framework that require no other
framework dependancies

"""
import copy
import re
import pprint
import json
from collections.abc import Mapping

from hashlib import sha512

__author__ = "Mike Stabile, Jeremy Nelson"


def pick(*args):
    """
    Returns the first non None value of the passed in values

    :param args:
    :return:
    """
    for item in args:
        if item is not None:
            return item
    return None


def nz(value, none_value, strict=True):
    """
    This function is named after an old VBA function. It returns a default
    value if the passed in value is None. If strict is False it will
    treat an empty string as None as well.

    :param value:
    :param none_value:
    :param strict:
    :return:

    :example:
        x = None  |  nz(x,"hello")          -->   "hello"
                     nz(x,"")               -->    ""
        y = ""    |  nz(y,"hello")          -->    ""
                     nz(y,"hello", False)   -->    "hello"
    """

    if value is None and strict:
        return_val = none_value
    elif strict and value is not None:
        return_val = value
    elif not strict and not is_not_null(value):
        return_val = none_value
    else:
        return_val = value
    return return_val


def cbool(value, strict=True):
    """
    converts a value to true or false. Python's default bool() function
    does not handle 'true' of 'false' strings

    :param value:
    :param strict:
    :return:
    """
    return_val = value
    if is_not_null(value):
        if isinstance(value, bool):
            return_val = value
        else:
            value = str(value)
            if value.lower() in ['true', '1', 't', 'y', 'yes']:
                return_val = True
            elif value.lower() in ['false', '0', 'n', 'no', 'f']:
                return_val = False
            else:
                if strict:
                    return_val = None
    else:
        if strict:
            return_val = None
    return return_val


def is_not_null(value):
    """
    test for None and empty string

    :param value:
    :return: True if value is not null/none or empty string
    """
    return value is not None and len(str(value)) > 0


def make_list(value):
    """
    Takes a value and turns it into a list if it is not one

    !!!!! This is important becouse list(value) if perfomed on an
    dictionary will return the keys of the dictionary in a list and not
    the dictionay as an element in the list. i.e.
        x = {"first":1, "second":2}
        list(x) = ["first", "second"]
        or use this [x,]
        make_list(x) =[{"first":1, "second":2}]

    :param value:
    :return:
    """
    if not isinstance(value, list):
        value = [value]
    return value


def make_set(value):
    """
    Takes a value and turns it into a set

    !!!! This is important because set(string) will parse a string to
    individual characters vs. adding the string as an element of
    the set i.e.
        x = 'setvalue'
        set(x) = {'t', 'a', 'e', 'v', 'u', 's', 'l'}
        make_set(x) = {'setvalue'}
        or use set([x,]) by adding string as first item in list.

    :param value:
    :return:
    """
    if isinstance(value, list):
        value = set(value)
    elif not isinstance(value, set):
        value = set([value,])
    return value


class Dot(object):
    """ Takes a dictionary and gets and sets values via a "." dot notation
    of the path

    args:
        dictionary: The dictionary object
        copy_dict: Boolean - True - (default) does a deepcopy of the dictionay
            before returning. False - maniplutes the passed in dictionary

    """
    def __init__(self, dictionary, copy_dict=True):
        self.obj = dictionary
        self.new_dict = {}
        self.copy_dict = copy_dict

    def get(self, prop):
        """ get the value off the passed in dot notation

        args:
            prop: a string of the property to retreive
                "a.b.c" ~ dictionary['a']['b']['c']
        """
        prop_parts = prop.split(".")
        val = None
        for part in prop_parts:
            if val is None:
                val = self.obj.get(part)
            else:
                val = val.get(part)
        return val

    def set(self, prop, value):
        """ sets the dot notated property to the passed in value

        args:
            prop: a string of the property to retreive
                "a.b.c" ~ dictionary['a']['b']['c']
            value: the value to set the prop object
        """

        prop_parts = prop.split(".")
        if self.copy_dict:
            new_dict = copy.deepcopy(self.obj)
        else:
            new_dict = self.obj
        pointer = None
        parts_length = len(prop_parts) - 1
        for i, part in enumerate(prop_parts):
            if pointer is None and i == parts_length:
                new_dict[part] = value
            elif pointer is None:
                pointer = new_dict.get(part)
            elif i == parts_length:
                pointer[part] = value
            else:
                pointer = pointer.get(part)
        return new_dict


def rep_int(value):
    """ takes a value and see's if can be converted to an integer

    Args:
        value: value to test
    Returns:
        True or False
    """

    try:
        int(value)
        return True
    except ValueError:
        return False


def delete_key_pattern(obj, regx_pattern):
    """
    takes a dictionary object and a regular expression pattern and removes
    all keys that match the pattern.

    args:
        obj: dictionay object to search trhough
        regx_pattern: string without beginning and ending /

    :param obj:
    :param regx_pattern:
    :return:
    """

    if isinstance(obj, list):
        _return_list = []
        for item in obj:
            if isinstance(item, list):
                _return_list.append(delete_key_pattern(item, regx_pattern))
            elif isinstance(item, set):
                _return_list.append(list(item))
            elif isinstance(item, dict):
                _return_list.append(delete_key_pattern(item, regx_pattern))
            else:
                try:
                    json.dumps(item)
                    _return_list.append(item)
                except:
                    _return_list.append(str(type(item)))
        return _return_list
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        _return_obj = {}
        for key, item in obj.items():
            if not re.match(regx_pattern, key):
                if isinstance(item, list):
                    _return_obj[key] = delete_key_pattern(item, regx_pattern)
                elif isinstance(item, set):
                    _return_obj[key] = list(item)
                elif isinstance(item, dict):
                    _return_obj[key] = delete_key_pattern(item, regx_pattern)
                else:
                    try:
                        json.dumps(item)
                        _return_obj[key] = item
                    except:
                        _return_obj[key] = str(type(item))
        return _return_obj
    else:
        try:
            json.dumps(obj)
            return obj
        except:
            return str(type(obj))


def get_dict_key(data, key):
    ''' will serach a mulitdemensional dictionary for a key name and return a
        value list of matching results '''

    if isinstance(data, Mapping):
        if key in data:
            yield data[key]
        for key_data in data.values():
            for found in get_dict_key(key_data, key):
                yield found


def get_attr(item, name, default=None):
    """
    similar to getattr and get but will test for class or dict

    :param item:
    :param name:
    :param default:
    :return:
    """
    try:
        val = item[name]
    except (KeyError, TypeError):
        try:
            val = getattr(item, name)
        except AttributeError:
            val = default
    return val


def get2(item, key, if_none=None, strict=True):
    """
    similar to dict.get functionality but None value will return then
        if_none value

    :param item: dictionary to search
    :param key: the dictionary key
    :param if_none: the value to return if None is passed in
    :param strict: if False an empty string is treated as None
    :return:
    """

    if not strict and item.get(key) == "":
        return if_none
    elif item.get(key) is None:
        return if_none
    else:
        return item.get(key)


class IsFirst:
    ''' tracks if is the first time through a loop. class must be initialized
        outside the loop.

        *args:
            true -> specifiy the value to return on true
            false -> specify to value to return on false    '''

    def __init__(self):
        self.__first = True

    def first(self, true=True, false=False):
        if self.__first == True:
            self.__first = False
            return true
        else:
            return false


class DictClassMeta(type):
    """ Used to handle list generation """

    def __call__(cls, *args, **kwargs):

        new_class = False
        if len(args) > 0:
            new_class = make_class(args[0], kwargs.get('debug',False))
        if new_class and isinstance(new_class, list):
            return new_class
        elif len(args) > 0:
            vals = list(args)
            vals[0] = new_class
            vals = tuple(vals)
        else:
            vals = args
        return super().__call__(*vals, **kwargs)


RESERVED_KEYS = ['dict',
                 'get',
                 'items',
                 'keys',
                 'values',
                 '_DictClass__reserved',
                 '_RdfConfigManager__reserved',
                 '_RdfConfigManager__type',
                 '_DictClass__type',
                 'debug',
                 '_RdfConfigManager__load_config']


class DictClass(metaclass=DictClassMeta):
    ''' takes a dictionary and converts it to a class '''
    __reserved = RESERVED_KEYS
    __type = 'DictClass'

    def __init__(self, obj=None, start=True, debug=False):
        if obj and start:
            for attr in dir(obj):
                if not attr.startswith('_') and attr not in self.__reserved:
                    setattr(self, attr, getattr(obj,attr))

    def __getattr__(self, attr):
        return None

    def __getitem__(self, item):
        item = str(item)
        if hasattr(self, item):
            return getattr(self, item)
        else:
            return None

    def __setitem__(self, attr, value):
        self.__setattr__(attr, value)

    def __str__(self):
        return str(self.dict())

    def __repr__(self):
        return "DictClass(\n%s\n)" % pprint.pformat(self.dict())

    def __setattr__(self, attr, value):
        if isinstance(value, dict) or isinstance(value, list):
            value = DictClass(value)
        self.__dict__[attr] = value

    def dict(self):
        """ converts the class to a dictionary object """
        return_obj = {}
        for attr in dir(self):
            if not attr.startswith('__') and attr not in self.__reserved:
                if isinstance(getattr(self, attr), list):
                    return_val = []
                    for item in getattr(self, attr):
                        if isinstance(item, DictClass):
                            return_val.append(dict(item))
                        else:
                            return_val.append(item)
                elif isinstance(getattr(self, attr), dict):
                    return_val = {}
                    for key, item in getattr(self, attr).items():
                        if isinstance(item, DictClass):
                            return_val[key] = item.dict()
                        else:
                            return_val[key] = item
                elif isinstance(getattr(self, attr), DictClass):
                    return_val = getattr(self, attr).dict()
                else:
                    return_val = getattr(self, attr)
                return_obj[attr] = return_val
        return return_obj

    def get(self, attr, none_val=None, strict=False):
        if attr in self.keys():
            if strict and self[attr] is None:
                return none_val
            else:
                return getattr(self, attr)
        else:
            return none_val

    def keys(self):
        return [attr for attr in dir(self) if not attr.startswith("__") and \
                attr not in self.__reserved]

    def values(self):
        return [getattr(self, attr) for attr in dir(self) if not attr.startswith("__") and \
                attr not in self.__reserved]

    def items(self):
        return_list = []
        for attr in dir(self):
            if not attr.startswith("__") and attr not in self.__reserved:
                return_list.append((attr, getattr(self, attr)))
        return return_list


def make_class(obj, debug=False):
    __reserved = RESERVED_KEYS
    if isinstance(obj, list):
        _return_list = []
        for item in obj:
            if isinstance(item, list):
                _return_list.append(make_class(item, debug))
            elif isinstance(item, set):
                _return_list.append(list(item))
            elif isinstance(item, dict):
                _return_list.append(make_class(item, debug))
            else:
                _return_list.append(item)
        return _return_list
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        new_dict = DictClass(start=False)
        for key, item in obj.items():
            if key in __reserved:
                key += "_1"
            if not key.startswith('__'):

                if isinstance(item, list):

                    setattr(new_dict, key, make_class(item, debug))
                elif isinstance(item, set):

                    setattr(new_dict, key, list(item))
                elif isinstance(item, dict):

                    setattr(new_dict, key, make_class(item, debug))
                else:

                    setattr(new_dict, key, item)
        return new_dict
    else:
        return obj


def first(item):
    """
    Return an empty dict or the first item in a list

    :param item:
    :return:
    """
    if isinstance(item, list):
        return {} if not item else item[0]
    return {}


def hash_email(email):
    """
    hashes the email for storing in the database

    :param email:
    :return: hashed email
    """
    return sha512(email.lower().strip().encode()).hexdigest()

