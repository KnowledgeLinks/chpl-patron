"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson, Mike Stabile"

import os
import re
import requests
import smtplib
import sqlite3
from email.mime.text import MIMEText
from flask import Flask, make_response, request, current_app, jsonify
from validate_email import validate_email
from hashlib import sha512
from dateutil.parser import parse as date_parse
from datetime import timedelta
from functools import update_wrapper

import chplpatron.geosearch as geosearch
from chplpatron import geosearch
from chplpatron import sierra
from chplpatron.exceptions import *

from .utilities import crossdomain
from .messages import InvalidMsgs

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile("config.py")

CURRENT_DIR = os.path.abspath(os.curdir)

CROSS_DOMAIN_SITE = app.config.get('CROSS_DOMAIN_SITE',
                                   "https://chapelhillpubliclibrary.org")
basestring = (str, bytes)


@app.route("/email_check")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_email_check(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    rtn_msg = email_check(email=request.args.get("g587-email", "").lower(),
                          debug=request.args.get("debug",False))
    return jsonify(rtn_msg)


@app.route("/postal_code")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_postal_code(**kwargs):
    """ gets the associated cities for the specified postal code
    """
    rtn_msg = postal_code(zipcode=request.args.get("g587-zipcode",""),
                          debug=request.args.get("debug",False))
    return jsonify(rtn_msg)


@app.route("/", methods=["POST"])
@crossdomain(origin=CROSS_DOMAIN_SITE)
def index():
    """Default view for handling post submissions from a posted form"""
    if not request.method.startswith("POST"):
        return "Method not supported"
    form = request.form.to_dict()
    valid_form = validate_form(form)
    if valid_form['valid']:
        temp_card_number = register_patron(valid_form['form'])
        if temp_card_number is not None:
            if request.remote_addr.startswith("198.85.222.29"):
                success_uri = app.config.get("INTERNAL_SUCCESS")
            else:
                success_uri = app.config.get("SUCCESS_URI")
            return jsonify({"valid": True,
                            "url": "{}?number={}".format(
                                  success_uri,
                                  temp_card_number)})
        else:
            return jsonify({"valid": True,
                            "url": "{}?error={}".format(
                                    app.config.get("ERROR_URI"),
                                    "Failed to register Patron")})
    else:
        return jsonify(valid_form)


@app.route("/test_form", methods=['GET', 'POST'])
def test_form():
    form_path = os.path.join(CURRENT_DIR, "wordpress", "currentform.txt")
    html = ""
    with open(form_path, "r") as form_file:
        html = form_file.read()
    return html.replace("104.131.189.93", "localhost")


if __name__ == '__main__':
    print("Starting Chapel Hills Patron Registration")
    app.run(host='0.0.0.0', port=4000, debug=True)
