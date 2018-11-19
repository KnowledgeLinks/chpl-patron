import json
import requests
import instance

def get_token():
    header = {
        "Authorization": f"Basic {instance.API_KEY}", 
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(instance.TOKEN_URL, headers=header)
    return response.json().get("access_token")


def register(payload):
    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json"
    } 
    result = requests.post(instance.PATRON_URL)
