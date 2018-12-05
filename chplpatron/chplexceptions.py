import pprint

from simplejson.errors import JSONDecodeError


class InvalidPostalCode(Exception):
    def __init__(self, postal_code):
        self.postal_code = postal_code
        super().__init__("'{}' is an invalid postal code".format(postal_code))


class InvalidState(Exception):
    def __init__(self, state):
        self.state = state
        super().__init__("'{}' is an invalid US state".format(state))


class InvalidCity(Exception):
    def __init__(self, city):
        self.city = city
        super().__init__("'{}' is an invalid City".format(city))


class TokenError(Exception):
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        super().__init__("Unable to retrieve token with key '{}'".format(key))

class RemoteApiError(Exception):
    def __init__(self, url, response):
        self.response = response
        try:
            text = pprint.pformat(response.json())
        except JSONDecodeError:
            text = response.text
        super().__init__("\n\turl: {}"
                         "\n\tstatus_code: {}"
                         "\n\ttext: {}".format(url,
                                               response.status_code,
                                               text))


class RegisteredEmailError(Exception):
    def __init__(self, email):
        self.email = email
        super().__init__("Email was previously registered: {}"
                         .format(email))
