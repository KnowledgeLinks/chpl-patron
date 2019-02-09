"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson, Mike Stabile"

import os
import sys
import logging

from logging.handlers import RotatingFileHandler

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
from chplpatron import exceptions

from instance import config

app = Flask(__name__)
app.config.from_mapping()
app.config.from_object(config)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

LOG_FMT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
formatter = logging.Formatter(LOG_FMT)
logging.basicConfig(level=logging.DEBUG,
                    format=LOG_FMT,
                    datefmt='%m-%d %H:%M')
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
log = app.logger
log.setLevel(logging.INFO)
LOG_PATH = os.path.abspath("../../logging") \
           if not hasattr(config, 'LOG_PATH') \
           else config.LOG_PATH
os.makedirs(LOG_PATH, exist_ok=True)
error_handler = RotatingFileHandler(os.path.join(LOG_PATH, "errors.log"),
                                    maxBytes=10 * 1024 * 1024,
                                    backupCount=5)
info_handler = RotatingFileHandler(os.path.join(LOG_PATH, "general.log"),
                                   maxBytes=10 * 1024 * 1024,
                                   backupCount=5)
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# console_handler.setLevel(logging.DEBUG)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
log.addHandler(error_handler)
# log.addHandler(console_handler)
log.addHandler(info_handler)
log.setLevel(logging.INFO)

HIDE = ['SECRET_KEY']
log.info("##### CONFIGURATION VALUES ###################\n%s" % \
         "\n".join(["\t\t\t%s: %s" % (key, value)
                    for key, value in app.config.items()
                    if key not in HIDE]))

CURRENT_DIR = os.path.abspath(os.curdir)

CROSS_DOMAIN_SITE = "https://chapelhillpubliclibrary.org" \
                    if not hasattr(config, 'CROSS_DOMAIN_SITE') \
                    else config.CROSS_DOMAIN_SITE

basestring = (str, bytes)


@app.route("/register/boundary_check")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_boundary_check(**kwargs):
    """
    Checks to see if the address is within the CHPL boundary
    :param kwargs:
    :return:
    """
    try:
        lookup = kwargs if kwargs else request.args
        address = {'street': lookup.get(Flds.street.frm),
                   'city': lookup.get(Flds.city.frm),
                   'state': lookup.get(Flds.state.frm),
                   'postal_code': lookup.get(Flds.postal_code.frm)}
        rtn_msg = boundary_check(**address)
        return rtn_msg if kwargs else jsonify(rtn_msg)
    except Exception as err:
        log.exception(err)


@app.route("/register/email_check")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_email_check():
    """
    Checks to see if the email address as has already been registered

    request args:
        g587-email: the email address to check
    """
    try:
        rtn_msg = email_check(email=request.args.get(Flds.email.frm, ""),
                              debug=request.args.get("debug", False))
        if rtn_msg['valid']:
            return jsonify(True)
        return jsonify(rtn_msg['message'])
    except Exception as err:
        log.exception(err)


@app.route("/register/validate_password")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_validate_password():
    """
    gets the associated cities for the specified postal code
    """
    try:
        rtn_msg = validate_password(request.args.get(Flds.password.frm, ""))
        if rtn_msg['valid']:
            return jsonify(True)
        return jsonify(rtn_msg['message'])
    except Exception as err:
        log.exception(err)


@app.route("/register/postal_code")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_postal_code():
    """
    gets the associated cities for the specified postal code
    """
    try:
        rtn_msg = postal_code(zipcode=request.args.get(Flds.postal_code.frm,
                                                       ""),
                              debug=request.args.get("debug", False))
        return jsonify(rtn_msg)
    except Exception as err:
        log.exception(err)


@app.route("/register", methods=["POST"])
@crossdomain(origin=CROSS_DOMAIN_SITE)
def index():
    """
    Default view for handling post submissions from a posted form

    """
    try:
        if not request.method.startswith("POST"):
            return "Method not supported"
        form = request.form.to_dict()
        testing = testing_mode(form)
        valid_form = validate_form(form)

        if valid_form['valid']:
            lookup = form
            address = {'street': lookup.get(Flds.street.frm),
                       'city': lookup.get(Flds.city.frm),
                       'state': lookup.get(Flds.state.frm),
                       'postal_code': lookup.get(Flds.postal_code.frm)}

            boundary = boundary_check(**address)
            location = "internal" if request.remote_addr \
                       and request.remote_addr.startswith(config.INTERNAL_IP) \
                       else "external"
            try:
                temp_card_number = "testing"
                if not testing:
                    temp_card_number = register_patron(valid_form['form'],
                                                       location,
                                                       boundary)
                if temp_card_number is not None:
                    if location == "internal":
                        success_uri = config.INTERNAL_SUCCESS
                    else:
                        success_uri = config.SUCCESS_URI
                    return jsonify({"valid": True,
                                    "url": "{}?number={}&boundary={}".format(
                                          success_uri,
                                          temp_card_number,
                                          boundary['valid'])})
            except exceptions.PasswordError as p_err:
                # log.exception(p_err)
                error_obj = {"field": Flds.password.frm,
                             "valid": False,
                             "message": p_err.msg}
                valid_form['errors'].append(error_obj)
                valid_form['valid'] = False
                return jsonify(valid_form)
            except Exception as err1:
                log.exception(err1.with_traceback())
                log.error({key: value
                           for key, value in form.items()
                           if "password" not in key.lower()})
            return jsonify({"valid": True,
                            "url": "{}?error={}".format(
                                    config.ERROR_URI,
                                    "Failed to register Patron")})
        else:
            return jsonify(valid_form)
    except Exception as err:
        log.exception(err)
        log.error({key: value
                   for key, value in form.items()
                   if "password" not in key.lower()})
        return jsonify({"valid": True,
                        "url": "{}?error={}".format(config.ERROR_URI,
                                                    ("Failed to register "
                                                     "Patron"))})


# @app.route("/test_form", methods=['GET', 'POST'])
# @crossdomain(origin=CROSS_DOMAIN_SITE)
# def test_form():
#     form_path = os.path.join(os.path.abspath("../../"),
#                              "wordpress",
#                              "currentform.txt")
#     # html = ""
#     with open(form_path, "r") as form_file:
#         html = form_file.read()
#     return html.replace("104.131.189.93", "localhost")
def testing_mode(form):
    try:
        return form.pop("testing")
    except KeyError:
        return False


@app.route("/register/statistics", methods=['GET', 'POST'])
@crossdomain(origin=CROSS_DOMAIN_SITE)
def statistics():
    form_path = os.path.join(os.path.abspath("../../"),
                             "wordpress",
                             "statistics.html")
    # html = ""
    with open(form_path, "r") as form_file:
        html = form_file.read()
    return html.replace("104.131.189.93", "localhost")

# @app.route("/register", methods=["GET"])
# def test_routing():
#    return jsonify({"app": "running"})

# @app.route("/database", methods=['GET'])
# @crossdomain(origin=CROSS_DOMAIN_SITE)
# def database_data():
#     template = ("<html>"
#                 "<body>"
#                 "<h1>Database data</h1>"
#                 "<table>"
#                 "<tr>{header_row}</tr>"
#                 "{data_rows}"
#                 "</table>"
#                 "</body>"
#                 "</html>")
#     # trackingdb.trackingdb.load_old_d
#
#     header_row = "".join(["<th>{}</th>".format(item)
#                           for item in trackingdb.columns()])
#     data_rows = "\n".join(["<tr><td>{}</td></tr>"
#                            .format("</td><td>".join([str(i) for i in item]))
#                            for item in trackingdb.get_data()])
#     return template.format(header_row=header_row,
#                            data_rows=data_rows)


@app.route("/register/statistics/reg_by_month")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def reg_by_month():
    data = trackingdb.registration_by_month()
    data = {"labels": [item[0] for item in data],
            "values": [item[1] for item in data]}
    return jsonify(data)


if __name__ == '__main__':
    context = ("../../instance/chapelhillpubliclibrary_org.crt",
               "../../instance/private_key.txt")
    print(os.path.abspath("../../"))
    sys.path.extend(os.path.abspath("../../"))
    print("Starting Chapel Hills Patron Registration")

    # app.run(host='0.0.0.0', port=8443, debug=True)
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=context)

