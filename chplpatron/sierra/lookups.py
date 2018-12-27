"""
Module providing lookup type information, i.e. urls, field names and
associated functions and classes
"""

import urllib
import requests

from enum import Enum

PRODUCTION_URL = ("https://catalog.chapelhillpubliclibrary.org/"
                  "iii/sierra-api/v5/")
SANDBOX_URL = "https://sandbox.iii.com:443/iii/sierra-api/v5/"


class UrlMode(Enum):
    """
    Provides the options for different modes with associated url values.
    """
    production = PRODUCTION_URL
    sandbox = SANDBOX_URL


class ReqMethods(Enum):
    """
    Provides a list of allowed requests methods for use in the application
    """
    get = "get"
    post = "post"
    put = "put"
    delete = "delete"


class PatronFlds(Enum):
    """
    Enumerates the available fields for use with patron records
    """

    id = 'id'
    updatedDate = 'updatedDate'
    createdDate = 'createdDate'
    deletedDate = 'deletedDate'
    deleted = 'deleted'
    suppressed = 'suppressed'
    names = 'names'
    barcodes = 'barcodes'
    expirationDate = 'expirationDate'
    birthDate = 'birthDate'
    emails = 'emails'
    patronType = 'patronType'
    patronCodes = 'patronCodes'
    homeLibraryCode = 'homeLibraryCode'
    message = 'message'
    blockInfo = 'blockInfo'
    addresses = 'addresses'
    phones = 'phones'
    uniqueIds = 'uniqueIds'
    moneyOwed = 'moneyOwed'
    pMessage = 'pMessage'
    langPref = 'langPref'
    fixedFields = 'fixedFields'
    varFields = 'varFields'

    @classmethod
    def list_all(cls):
        """
        :return: a comma separated list of all fields
        """
        return ",".join([fld.name for fld in cls])



class ApiSpec:
    """
    Specifications for an API endpoint

    :param url: portion of the url to add to the base url
    :param method: ReqMethods option for the endpoint
    :param params: list of available parameters
    """
    __SLOTS__ = ["method", "params", "url"]
    methods = ReqMethods

    def __init__(self, url, method=methods.get, params=None):
        self.url = url
        self.params = params
        self.method = getattr(requests, method.value)


class ApiUrls(Enum):
    """
    Enumeration of available API endpoints and ApiSpecs
    """
    create_patron = ApiSpec("patrons", ReqMethods.post)
    patron_update = ApiSpec("patrons/{}",
                            ReqMethods.put)
    patron_get = ApiSpec("patrons/{}",
                         ReqMethods.get,
                         params=['fields'])
    delete_patron = ApiSpec("patrons/{}",
                            ReqMethods.delete)
    patron = ApiSpec("patrons",
                     ReqMethods.get,
                     params=['offset',
                             'limit',
                             PatronFlds.id.value,
                             'fields',
                             PatronFlds.createdDate.value,
                             PatronFlds.updatedDate.value,
                             PatronFlds.deletedDate.value,
                             PatronFlds.deleted.value,
                             PatronFlds.suppressed.value,
                             'agencyCodes'])
    query = ApiSpec("patrons/query",
                    ReqMethods.post,
                    params=['offset', 'limit'])
    find = ApiSpec("patrons/find", params=['varFieldTag',
                                           'varFieldContent',
                                           'fields'])
    token = ApiSpec("token",
                    ReqMethods.post)
    token_info = ApiSpec("info/token")


class Apis:
    """
    call the specified API with supplied paramaters

    :param url_mode: ["production", "sandbox"] specifies which base url to use

    :usage:
        apis.[ApiUrls name](parameters, **kwargs)

    :example:
        apis = Apis("production")
        response = apis.find(params=["n", "DOE, JOHN], headers=headers)
        print(response.text)
            "data of a requests text attribute" 
    """
    modes = UrlMode
    base_url = modes.production
    api_specs = ApiUrls

    def __init__(self, url_mode="production"):
        self.base_url = getattr(self.modes, url_mode)

    def __getattr__(self, item):
        try:
            return self.__getattribute__(item)
        except AttributeError:
            spec = getattr(self.api_specs, item)
            try:
                return ApiCaller(spec, self.base_url.value)
            except AttributeError:
                return ApiCaller(spec, self.base_url)


class ApiCaller:
    """
    calls the API with the supplied parameters and data
    """
    def __init__(self, api_spec, base_url):
        self.api_spec = api_spec
        self.base_url = base_url
        self.key = False
        self.key_val = None
        self.method = api_spec.value.method

        if "{}" in self.api_spec.value.url:
            self.key = True

    def __call__(self,
                 params=None,
                 data=None,
                 json=None,
                 headers=None,
                 **kwargs):
        self.params = params
        self.data = data
        self.json = json
        self.headers = headers
        req_kwargs = self.make_req_kwargs(**kwargs)
        url = self.format_url()
        return self.method(url, **req_kwargs)

    def make_req_kwargs(self, **kwargs):
        if not isinstance(kwargs, dict):
            kwargs = {}
        if self.data:
            kwargs['data'] = self.data
        if self.json:
            kwargs['json'] = self.json
        if self.headers:
            kwargs['headers'] = self.headers
        return kwargs

    def format_url(self):
        """
        Formats the url
        :return: a formatted url
        """

        params = self.format_params()
        url = "{}{}".format(self.base_url, self.api_spec.value.url)
        if self.key:
            if not self.key_val:
                raise UrlMissingKeyId(self.api_spec, self.params)
            url = url.format(self.key_val)
        if params:
            url = "{}?{}".format(url, params)
        return url

    def format_params(self):
        """
        Formats the supplied parameters

        :return: formatted parameters string
        """
        params = None
        if self.params:
            if isinstance(self.params, list):
                if self.key and not self.key_val:
                    self.key_val = self.params.pop(0)
                params = [urllib.parse.quote_plus(str(item))
                          for item in self.params]
                if not params:
                    return None
                try:
                    params = zip(self.api_spec.value.params, params)
                except TypeError:
                    raise InvalidParameter(self.api_spec.name,
                                           self.api_spec.value.params,
                                           self.params)
                params = "&".join(["{}={}".format(*param)
                                   for param in params
                                   if len(param) > 1 and param[1] is not None])
            elif isinstance(self.params, dict):
                if self.key and not self.key_val:
                    self.key_val = self.params.pop("key")
                params = "&".join(["{}={}"
                                  .format(key, urllib.parse.quote_plus(value))
                                   for key, value in self.params.items()])
            else:
                if self.key and not self.key_val:
                    self.key_val = self.params
                else:
                    params = self.params
        return params


class InvalidParameter(Exception):
    """
    Exception for a parameter violation
    """
    def __init__(self, name, allowed, supplied):
        if not isinstance(allowed, list):
            super().__init__("No parameters are allowed in '{}'".format(name))
        else:

            super().__init__(("Parameters in '{}'\n"
                              "\tNot allowed: {}\n"
                              "\tAllowed: {}")
                             .format(name,
                                     set(supplied).difference(set(allowed)),
                                     allowed))


class UrlMissingKeyId(Exception):
    def __init__(self, api_spec, params):
        self.api_spec = api_spec
        self.params = params
        super().__init__("Key id not supplied for api '{}' with url '{}' "
                         "passed in params were: {}"
                         .format(api_spec.name, api_spec.value.url, params))
