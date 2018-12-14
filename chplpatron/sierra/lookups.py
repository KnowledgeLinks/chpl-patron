"""
Module providing lookup type information, i.e. urls, field names and
associated functions and classes
"""

import urllib

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
        self.method = method


class ApiUrls(Enum):
    """
    Enumeration of available API endpoints and ApiSpecs
    """
    create_patron = ApiSpec("patrons", ReqMethods.post)
    patron_update = ApiSpec("patrons/{}",
                            ReqMethods.put)
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
    token = ApiSpec("token")
    token_info = ApiSpec("info/token")


class Urls:
    """
    Url formatting class for specified API endpoints

    :param url_mode: ["production", "sandbox"] specifies which base url to use

    :usage:
        url.[ApiUrls name](parameters)

    :example:
        url = Urls("production")
        req_url = url.find(["n", "DOE, JOHN])
        print(req_url)
        'https://.../../patrons/find?varFieldTag=n&varFieldContent=DOE%2C+JOHN'
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
                return UrlFormatter(spec, self.base_url.value)
            except AttributeError:
                return UrlFormatter(spec, self.base_url)


class UrlFormatter:
    """
    Formats urls with the supplied parameters
    """
    def __init__(self, api_spec, base_url):
        self.api_spec = api_spec
        self.base_url = base_url
        self.key = False
        self.key_val = None
        if "{}" in self.api_spec.value.url:
            self.key = True

    def __call__(self, params=None, data=None):
        self.params = params
        self.data = data
        return self.format_url()

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