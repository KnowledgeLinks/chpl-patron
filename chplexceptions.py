class InvalidPostalCode(Exception):
    def __init__(self, message):
        super().__init__("'{}' is an invalid postal code".format(message))


class InvalidState(Exception):
    def __init__(self, message):
        super().__init__("'{}' is an invalid US state".format(message))


class InvalidCity(Exception):
    def __init__(self, message):
        super().__init__("'{}' is an invalid City".format(message))


class RemoteApiError(Exception):
    def __init__(self, url, response):
        super().__init__("\n\turl: {}"
                         "\n\tstatus_code: {}"
                         "\n\ttext: {}".format(url,
                                               response.status_code,
                                               response.text))

