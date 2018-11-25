import base64
import json
import requests
import instance

SIERRA_API = "https://catalog.chapelhillpubliclibrary.org/iii/sierra-api/v5/"
# SIERRA_API = "https://sandbox.iii.com:443/iii/sierra-api/v5/patrons/"

PATRON_URL = "{0}patrons/".format(SIERRA_API)
TOKEN_URL = "{0}token".format(SIERRA_API)


def get_token():
    encoded_key = base64.b64encode("{}:{}".format(instance.API_KEY, 
        instance.CLIENT_SECRET).encode())
    headers = {
       "Authorization": "Basic {}".format(encoded_key), 
       "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(TOKEN_URL, headers=headers)
    import pdb; pdb.set_trace()
    if response.status_code < 399:
        return response.json().get("access_token")
    raise ValueError("{} get_token request status code: {}".format(
        TOKEN_URL,
        response.status_code),
        response.text)


def register(payload):
    headers = {
        "Authorization": "Bearer {}".format(get_token()),
        "Content-Type": "application/json"
    } 
    result = requests.posti(PATRON_URL)
