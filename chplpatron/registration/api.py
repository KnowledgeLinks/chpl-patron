"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson, Mike Stabile"

import os
import sys
import pprint

from flask import (Flask,
                   request,
                   jsonify)

print(os.path.abspath("../../"))
sys.path.append(os.path.abspath("../../"))

from chplpatron.registration.utilities import crossdomain, Flds
from chplpatron.registration.validation import (validate_form,
                                                email_check,
                                                postal_code,
                                                boundary_check,
                                                validate_password)
from chplpatron.registration.actions import register_patron
from chplpatron import trackingdb

from instance import config

app = Flask(__name__)
app.config.from_mapping()
app.config.from_object(config)

app.config.INTERNAL_IP = "198.85.222.29"

print("##### CONFIGURATION VALUES ###################")
pprint.pprint(app.config)
print("##############################################")

CURRENT_DIR = os.path.abspath(os.curdir)

CROSS_DOMAIN_SITE = app.config.get('CROSS_DOMAIN_SITE',
                                   "https://chapelhillpubliclibrary.org")
basestring = (str, bytes)


@app.route("/boundary_check")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_boundary_check(**kwargs):
    """
    Checks to see if the address is within the CHPL boundary
    :param kwargs:
    :return:
    """
    address = kwargs
    if request.args.get(Flds.street.frm):
        address = {'street': request.args.get(Flds.street.frm),
                   'city': request.args.get(Flds.city.frm),
                   'state': request.args.get(Flds.state.frm),
                   'postal_code': request.args.get(Flds.postal_code.frm)}
    rtn_msg = boundary_check(**address)
    return jsonify(rtn_msg)


@app.route("/email_check")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_email_check(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    rtn_msg = email_check(email=request.args.get(Flds.email.frm, "").lower(),
                          debug=request.args.get("debug", False))
    if rtn_msg['valid']:
        return jsonify(True)
    return jsonify(rtn_msg['message'])


@app.route("/validate_password")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_validate_password(**kwargs):
    """
    gets the associated cities for the specified postal code
    """
    rtn_msg = validate_password(request.args.get(Flds.password.frm, ""))
    if rtn_msg['valid']:
        return jsonify(True)
    return jsonify(rtn_msg['message'])


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
        temp_card_number = register_patron(valid_form['form'],
                                           "internal"
                                           if request
                                           .remote_addr
                                           .startswith(app.config
                                                       .get("INTERNAL_IP")) else
                                           "external")
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
@crossdomain(origin=CROSS_DOMAIN_SITE)
def test_form():
    form_path = os.path.join(os.path.abspath("../../"),
                             "wordpress",
                             "currentform.txt")
    html = ""
    with open(form_path, "r") as form_file:
        html = form_file.read()
    return html.replace("104.131.189.93", "localhost")


@app.route("/statistics", methods=['GET', 'POST'])
@crossdomain(origin=CROSS_DOMAIN_SITE)
def statistics():
    form_path = os.path.join(os.path.abspath("../../"),
                             "wordpress",
                             "statistics.html")
    html = ""
    with open(form_path, "r") as form_file:
        html = form_file.read()
    return html.replace("104.131.189.93", "localhost")


@app.route("/database", methods=['GET'])
@crossdomain(origin=CROSS_DOMAIN_SITE)
def database_data():
    template = ("<html>"
                "<body>"
                "<h1>Database data</h1>"
                "<table>"
                "<tr>{header_row}</tr>"
                "{data_rows}"
                "</table>"
                "</body>"
                "</html>")
    # trackingdb.trackingdb.load_old_d

    header_row = "".join(["<th>{}</th>".format(item)
                          for item in trackingdb.columns()])
    data_rows = "\n".join(["<tr><td>{}</td></tr>"
                           .format("</td><td>".join([str(i) for i in item]))
                           for item in trackingdb.get_data()])
    return template.format(header_row=header_row,
                           data_rows=data_rows)


@app.route("/statistics/reg_by_month")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def reg_by_month():
    data = trackingdb.registration_by_month()
    data = {"labels": [item[0] for item in data],
            "values": [item[1] for item in data]}
    return jsonify(data)


if __name__ == '__main__':
    print(os.path.abspath("../../"))
    sys.path.extend(os.path.abspath("../../"))
    print("Starting Chapel Hills Patron Registration")
    app.run(host='0.0.0.0', port=3500, debug=True)
