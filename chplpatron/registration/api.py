"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson, Mike Stabile"

import os
import sys



from flask import (Flask,
                   make_response,
                   request,
                   current_app,
                   jsonify)

print(os.path.abspath("../../"))
sys.path.append(os.path.abspath("../../"))
import instance

from chplpatron.registration.utilities import crossdomain, Flds
from chplpatron.registration.validation import (validate_form,
                                                email_check,
                                                postal_code)
from chplpatron.registration.actions import register_patron


app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping()
app.config.INTERNAL_IP = "198.85.222.29"

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
    rtn_msg = email_check(email=request.args.get(Flds.email.frm, "").lower(),
                          debug=request.args.get("debug", False))
    return jsonify(rtn_msg)


@app.route("/postal_code")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_postal_code(**kwargs):
    """
    gets the associated cities for the specified postal code
    """
    rtn_msg = postal_code(zipcode=request.args.get(Flds.postal_code.frm, ""),
                          debug=request.args.get("debug", False))
    return jsonify(rtn_msg)


@app.route("/", methods=["POST"])
@crossdomain(origin=CROSS_DOMAIN_SITE)
def index():
    """
    Default view for handling post submissions from a posted form

    """
    if not request.method.startswith("POST"):
        return "Method not supported"
    form = request.form.to_dict()
    valid_form = validate_form(form)
    if valid_form['valid']:
        temp_card_number = register_patron(valid_form['form'])
        if temp_card_number is not None:
            if request.remote_addr.startswith(app.config.get("INTERNAL_IP")):
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
    form_path = os.path.join(os.path.abspath("../../"),
                             "wordpress",
                             "currentform.txt")
    html = ""
    with open(form_path, "r") as form_file:
        html = form_file.read()
    return html.replace("104.131.189.93", "localhost")


if __name__ == '__main__':
    print(os.path.abspath("../../"))
    sys.path.extend(os.path.abspath("../../"))
    print("Starting Chapel Hills Patron Registration")
    app.run(host='0.0.0.0', port=4000, debug=True)
