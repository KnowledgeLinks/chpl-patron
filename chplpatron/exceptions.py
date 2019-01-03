import pprint

from simplejson.errors import JSONDecodeError

RESPONSE_TEMPLATE = ("\n\turl: {}"
                     "\n\tstatus_code: {}"
                     "\n\ttext: {}")


def get_text(response):
    """
    Returns the best looking text from a response
    :param response:
    :return: string
    """
    try:
        return pprint.pformat(response.json())
    except JSONDecodeError:
        return pprint.pformat(response.text)


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
    def __init__(self,
                 key,
                 secret,
                 response,
                 message="Unable to retrieve token:"):
        self.key = key
        self.secret = secret
        self.response = response
        super().__init__("{}\n\tkey: '{}'{}"
                         .format(message,
                                 key,
                                 RESPONSE_TEMPLATE.format(response.url,
                                                          response.status_code,
                                                          get_text(response))))


class RemoteApiError(Exception):
    def __init__(self, response):
        self.response = response
        super().__init__(RESPONSE_TEMPLATE.format(response.url,
                                                  response.status_code,
                                                  get_text(response)))


class PasswordError(Exception):
    def __init__(self, response):
        self.response = response
        msg = response.json().get("description", "Password is not valid")
        self.msg = msg.replace("PIN", "Password")
        super().__init__(self.msg)


class RegisteredEmailError(Exception):
    def __init__(self, email):
        self.email = email
        super().__init__("Email was previously registered: {}"
                         .format(email))




