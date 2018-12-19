import base64
import requests
import instance
import datetime
import json
from chplpatron.exceptions import (RemoteApiError,
                                   RegisteredEmailError,
                                   TokenError)
from .lookups import (Apis,
                      PatronFlds)

APIS = Apis("production")  # "sandbox"
TOKEN = None
# the time that the token expires
TOKEN_TIME = datetime.datetime.now()
REQ_TOKEN_ROLES = {'Patrons_Read', 'Patrons_Write'}


def get_headers():
    """
    Gets the base headers for all api requests

    :return: header dictionary
    """
    return {"Authorization": get_token(),
            "Content-Type": "application/json"}


def get_token(error=False):
    """
    Retrieves a token to be used with all API request granting authorization.
    The roles associated with the with are verified against the REQ_TOKEN_ROLES
    set.

    :param error: If true will cause a request for a new token
    :return: the token or raises a TokenError
    """

    global TOKEN
    global TOKEN_TIME
    if TOKEN and datetime.datetime.now() < TOKEN_TIME and not error:
        return TOKEN
    encoded_key = base64.b64encode("{}:{}".format(instance.API_KEY, 
                                   instance.CLIENT_SECRET).encode())
    headers = {
       "Authorization": "Basic {}".format(encoded_key.decode()), 
       "Content-Type": "application/x-www-form-urlencoded"
    }
    response = APIS.token(headers=headers,
                          data="grant_type=client_credentials")
    
    if response.status_code < 399:
        try:
            TOKEN = "{token_type} {access_token}".format(**response.json())
            expires = response.json().get("expires_in") - 10
            TOKEN_TIME = datetime.datetime.now() \
                + datetime.timedelta(seconds=expires)
            # Test to see if the token has the required roles/permissions
            token_info = get_token_info()
            token_roles = set([role.get('name')
                               for role in token_info.get('roles', [{}])
                               if role.get('name')])
            missing_roles = REQ_TOKEN_ROLES.difference(token_roles)
            if missing_roles:
                raise TokenError(instance.API_KEY,
                                 instance.CLIENT_SECRET,
                                 response,
                                 "Missing Roles: {}".format(missing_roles))
            return TOKEN
        except Exception as err:
            if isinstance(err, TokenError):
                raise err
    raise TokenError(instance.API_KEY,
                     instance.CLIENT_SECRET,
                     response)


def get_token_info():
    """
    Returns the information pertaining to the supplied token

    :return: dictionary of token information
    """
    result = APIS.token_info(headers=get_headers())
    return result.json()


def delete_patron(patron_id):
    result = APIS.delete_patron(patron_id)


def create_patron(payload):

    result = APIS.create_patron(headers=get_headers(),
                                data=payload)
    return result


def lookup_by_email(email_value=None):
    """
    Lookup a Patron by their email address

    :param email_value: the email address to search for
    :return: dict: patron information
    """

    if not email_value:
        return {}

    email_value = email_value.strip().lower()
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

    result = APIS.query(params=[0, 1], headers=headers, json=json_qry)
    if result.status_code != 200:
        raise RemoteApiError(result)
    for link in result.json().get('entries', []):
        response = requests.get("{0}?fields={1}".format(link['link'],
                                                        PatronFlds.list_all()),
                                headers=headers)
        return response.json()
    return {}


def lookup_by_name(name=None):
    """
    Lookup a Patron by their email address

    :param name: the patron name to lookup
    :return: dict: patron information
    """

    if not name:
        return {}

    headers = get_headers()

    result = APIS.find(["n", name, PatronFlds.list_all()], headers=headers)
    if result.status_code != 200:
        raise RemoteApiError(result)
    return result.json()


def set_barcode(barcode, patron_id):
    """
    sets the barcode for the specified patron
    :param barcode:
    :param patron_id:
    :return: True if successful
    :raises: RemoteApiError on fail
    """

    data = {"barcodes": [str(barcode)]}
    result = APIS.patron_update(patron_id,
                                headers=get_headers(),
                                json=data)
    if result.status_code != 204:
        raise RemoteApiError(result)
    return True


def set_email(email, patron_id):
    """
    sets the email for the specified patron
    :param email:
    :param patron_id:
    :return: True if successful
    :raises: RemoteApiError on fail
    """

    data = {"emails": [email]}
    # data = {
    #     "varFields": [{"fieldTag": "z",
    #                    "content": email}]
    #         }
    data = json.dumps(data)
    result = APIS.patron_update(patron_id,
                                headers=get_headers(),
                                data=data)
    if result.status_code != 204:
        raise RemoteApiError(result)
    return True


def check_email(email_value=None):
    """
    Tests to see if the email has already been registered

    :param email_value: the email address to search for

    :return: True if email is not registered else raises a RegisteredEmailError
    """
    if not email_value:
        return True
    patron_dict = lookup_by_email(email_value)
    emails = patron_dict.get("emails", [])
    for email in emails:
        if email.lower() == email_value:
            raise RegisteredEmailError(email_value)
    return True
