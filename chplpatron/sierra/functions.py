import base64
import requests
import instance
import pprint

from chplpatron.chplexceptions import (RemoteApiError,
                                       RegisteredEmailError,
                                       TokenError)
from .lookups import (Urls,
                      PatronFlds)

URLS = Urls()
TOKEN = None


def get_headers():
    return {"Authorization": get_token(),
            "Content-Type": "application/json"}


def get_token(error=False):
    global TOKEN
    if TOKEN and not error:
        return TOKEN
    encoded_key = base64.b64encode("{}:{}".format(instance.API_KEY, 
                                   instance.CLIENT_SECRET).encode())
    headers = {
       "Authorization": "Basic {}".format(encoded_key.decode()), 
       "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(URLS.token(),
                             headers=headers,
                             data="grant_type=client_credentials")
    
    if response.status_code < 399:
        try:
            TOKEN = "{token_type} {access_token}".format(**response.json())
        except KeyError:
            raise TokenError(instance.API_KEY, instance.CLIENT_SECRET)
        return TOKEN
    raise RemoteApiError(URLS.token(), response)


def get_token_info():
    result = requests.get(URLS.token_info(), headers=get_headers())
    pprint.pprint(result.json())
    return result.json()


def register(payload):
    result = requests.post(URLS.create_patron(), headers=get_headers(), data=payload)
    return result


def email_check(email_value=None):
    """Tests to see if the email has already been registered

    args:
        email_value: the email address to search for

    returns:
        True: if email is not registered
    """
    if not email_value:
        return True
    headers = get_headers()

    json_qry = {
        "target": {
            "record": {"type": "patron"},
            "field": {"tag": "z"}
        },
        "expr": {
            "op": "equals",
            "operands": [email_value]
        }
    }
    url = URLS.query([0, 1])
    result = requests.post(url, headers=headers, json=json_qry)
    if result.status_code != 200:
        raise RemoteApiError(url, result)
    sierra_email = None
    for link in result.json().get('entries', []):
        response = requests.get("{0}?fields=emails".format(link['link']),
                                headers=headers)
        sierra_email = response.json().get("emails", [None])[0]
    if sierra_email is not None \
            and sierra_email.lower() == email_value.lower():
        raise RegisteredEmailError(email_value)
    return True
