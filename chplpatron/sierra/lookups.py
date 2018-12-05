import urllib

from enum import Enum

PRODUCTION_URL = ("https://catalog.chapelhillpubliclibrary.org/"
                  "iii/sierra-api/v5/")
SANDBOX_URL = "https://sandbox.iii.com/iii/sierra-api/swagger/"


class UrlMode(Enum):
    production = PRODUCTION_URL
    sandbox = SANDBOX_URL


class ReqMethods(Enum):
    get = "get"
    post = "post"


class PatronFlds(Enum):
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
        return ",".join([fld.name for fld in cls])


class ApiSpec:
    __SLOTS__ = ["method", "params", "url"]
    methods = ReqMethods

    def __init__(self, url, method=methods.get, params=None):
        self.url = url
        self.params = params
        self.method = method


class ApiUrls(Enum):
    create_patron = ApiSpec("patrons", ReqMethods.post)
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
    Formats urls with supplied UrlMode
    """
    modes = UrlMode
    base_url = modes.production
    api_specs = ApiUrls

    def __init__(self, url_mode="production"):
        _base_url = getattr(self.modes, url_mode)

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
    def __init__(self, api_spec, base_url):
        self.api_spec = api_spec
        self.base_url = base_url

    def __call__(self, params=None, data=None):
        self.params = params
        self.data = data
        return self.format_url()

    def format_url(self):
        params = self.format_params()
        url = "{}{}".format(self.base_url, self.api_spec.value.url)
        if params:
            url = "{}?{}".format(url, params)
        # if self.api_spec.method == ReqMethods.post:
        return url

    def format_params(self):
        params = None
        if self.params:
            if isinstance(self.params, list):
                params = [urllib.parse.quote_plus(str(item))
                          for item in self.params]
                try:
                    params = zip(self.api_spec.value.params, params)
                except TypeError:
                    raise InvalidParameter(self.api_spec.name,
                                           self.api_spec.value.params,
                                           self.params)
                params = "&".join(["{}={}".format(*param)
                                   for param in params
                                   if len(param) > 1 and param[1] is not None])
            if isinstance(self.params, dict):
                params = "&".join(["{}={}"
                                  .format(key, urllib.parse.quote_plus(value))
                                   for key, value in self.params.items()])
            if isinstance(self.params, str):
                params = self.params
        return params


class InvalidParameter(Exception):
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
