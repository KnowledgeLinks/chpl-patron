import base64
import json
import requests
import instance

from chplexceptions import RemoteApiError

SIERRA_API = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v5/"
# SIERRA_API = "https://sandbox.iii.com:443/iii/sierra-api/v5/patrons/"

PATRON_URL = "{0}patrons/".format(SIERRA_API)
TOKEN_URL = "{0}token".format(SIERRA_API)
EMAIL_URL = "{0}patrons/query?offset=0&limit=1".format(SIERRA_API)
TOKEN = None


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
    response = requests.post(TOKEN_URL, 
                             headers=headers,
                             data="grant_type=client_credentials")
    
    if response.status_code < 399:
        TOKEN = response.json().get("access_token")
        print(TOKEN)
        return TOKEN
    raise RemoteApiError(TOKEN_URL, response)


def get_headers():
    return {
                "Authorization": "Bearer {}".format(get_token()),
                "Content-Type": "application/json"
            }


def register(payload):

    result = requests.post(PATRON_URL, headers=get_headers())
    return result


def email_check(email_value=None):
    """Tests to see if the email has already been registered

    args:
        email_value: the email address to search for
    """
    api_url = "/v5/patrons/query?offset=0&limit=1"
    json_qry = {
                    "target": {
                        "record": {"type": "patron"},
                         "field": {"tag": "emails"}
                    },
                    "expr": {
                        "op": "equals",
                        "operands": [email_value]
                    }
                }

    result = requests.post(EMAIL_URL, headers=get_headers(), data=json_qry)
    return result
