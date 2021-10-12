"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson, Mike Stabile"

import csv
import os
import re
import requests
import smtplib
import sqlite3
import dateutil
from email.mime.text import MIMEText
from flask import Flask, make_response, request, current_app, jsonify, abort, redirect
from validate_email import validate_email
from hashlib import sha512
from dateutil.parser import parse as date_parse
from datetime import timedelta
from functools import update_wrapper

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile("config.py")

# determine if duplicate emails should be checked
DUPLICATE_EMAIL_CHECK = app.config.get("DUPLICATE_EMAIL_CHECK")

CURRENT_DIR = os.path.abspath(os.curdir)
DB_PATH = app.config.get("DB_PATH")
if DB_PATH is None:
    DB_PATH = os.path.join(
        CURRENT_DIR,
        "card-requests.sqlite")
CROSS_DOMAIN_SITE = app.config.get('CROSS_DOMAIN_SITE',
                                   "https://chapelhillpubliclibrary.org")
basestring = (str,bytes)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


def setup_db():
    """ checks to see if the database is setup and sets it up if it doesn't"""
    if not os.path.exists(DB_PATH):
        run_sql("db-schema.sql")
        setup_postalcodes()
    # update the database schema if needed to remove the unique email constraint
    db_updated_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='old_LibraryCardRequest'";
    con = sqlite3.connect(DB_PATH)
    cur =  con.cursor()
    exists = len(cur.execute(db_updated_query).fetchall()) > 0
    if not exists:
        run_sql("db-remove-unique-email-constraint.sql")
    

def run_sql(filename):
    """Runs the SQL found in the file

    args:
        filename: the name of the sql file to run
    """
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    with open(os.path.join(CURRENT_DIR, filename)) as script_fo:
        script = script_fo.read()
        cur.executescript(script)
    cur.close()
    con.close()


def setup_postalcodes():
    """Setups up the database with postal codes if not already added to the
    the database"""

    con = sqlite3.connect(DB_PATH)
    postalcodes_setup = False

    # test to see if the table exists
    qry = """SELECT name 
             FROM sqlite_master 
             WHERE type='table' AND name='postalcodes';"""

    cur = con.cursor()

    # get the row count... if the row count is small reload the table
    if bool(len(cur.execute(qry).fetchall())):
        count = cur.execute("SELECT count(*) FROM postalcodes;").fetchone()
        if count[0] > 1000:
            postalcodes_setup = True

    if not postalcodes_setup:
        delete_tbl_sql = "DROP TABLE IF EXISTS postalcodes"
        create_tbl_sql = """CREATE TABLE IF NOT EXISTS postalcodes (
                             id integer PRIMARY KEY AUTOINCREMENT NOT NULL,
                             postal_code text NOT NULL,
                             city text NOT NULL,
                             state_long text NOT NULL,
                             state_short text,
                             lat text,
                             long text
                            ) ;"""
        ins_qry = """INSERT INTO postalcodes 
                    (postal_code, 
                     city,
                     state_long, 
                     state_short, 
                     lat, 
                     long) 
                     VALUES (?,?,?,?,?,?)"""
        cur.execute(delete_tbl_sql)
        con.commit()
        cur.execute(create_tbl_sql)
        con.commit()

        # read the datafile and add to the database
        with open(os.path.join(CURRENT_DIR,"postalcodes","US.txt"), "r") as data:
            pcodes = list(csv.reader(data, delimiter='\t'))
            for ln in pcodes:
                cur.execute(ins_qry,(ln[1], ln[2], ln[3], ln[4], ln[9], ln[10]))
        con.commit()
        cur.close()
        con.close()

def email_notification(form):
    """Sends an email notification of new card request

    Args:
        db_result(list): List of data from the database query
    """
    email = form.get("g587-email","").lower().strip()
    body = """New Library Card Request
Name: {0} {1}
Birthday: {2}
Address: {3}, {4}, {5} {6}
Phone number: {7}
Email: {8}
Temporary Library Card Number: {9}
""".format(form.get("g587-firstname"),
           form.get("g587-lastname"),
           form.get("g587-birthday"),
           form.get("g587-address"),
           form.get("g587-city"),
           form.get("g587-state"),
           form.get("g587-zipcode"),
           form.get("g587-telephone"),
           email,
           form.get("temp_card_number")
          )
    msg = MIMEText(body)
    msg['Subject'] = "New Card Request"
    msg['From'] = app.config["EMAIL_SENDER"] 
    msg['To'] = ','.join(app.config["EMAIL_RECIPIENTS"])
    msg['To'] += ",{}".format(email)
    mail_server = smtplib.SMTP('localhost')
    mail_server.send_message(msg)
    mail_server.quit()

TEMP_CARD_RE = re.compile(r"Your barcode is: <b>\n(\w+)</b>")
def find_card_number(raw_html):
    """Takes raw HTML from III and searches for temporary barcode number in the
    result.

    Args:
        raw_html(str): Raw HTML from the result
    Returns:
        string: Temporary card number
    """
    result = TEMP_CARD_RE.search(raw_html)
    if result is not None:
        return result.groups()[0]


def pin_reset(temp_pin):
    """Takes a temporary pin and calls III's PIN reset form and returns message
    if successful.

    Args:
        temp_pin(str): Temporary card pin

    Returns:
        string: PIN Reset
    """
    pin_reset_result = requests.post(app.config.get("PIN_RESET_URL"),
        data={"code": temp_pin})
    if pin_reset_result.status_code > 399:
        return False
    return True
     
 
def register_patron(form):
    """send the patron data to iii and adds a hash of the registered email
    to the local sqlite db

    Args:
        form
    """
    addr_string = form.get("g587-address")
    addr_string2 = "{}, {} {}".format(
        form.get("g587-city"),
        form.get("g587-state"),
        form.get("g587-zipcode"))
    data =  {
                "nfirst": form.get("g587-firstname"), 
                "nlast": form.get("g587-lastname"),
                "F051birthdate": form.get("g587-birthday"),
                "full_aaddress": [addr_string, addr_string2],
                "tphone1": form.get("g587-telephone"),
                "zemailaddr": form.get("g587-email","").lower().strip()
            }

    email_hash = sha512(form.get("g587-email","").lower().strip().encode()).hexdigest()   
    headers={"Cookie": 'SESSION_LANGUAGE=eng; SESSION_SCOPE=0; III_EXPT_FILE=aa31292'}
    add_patron_result = requests.post(app.config.get('SIERRA_URL'),
                                       data=data,
                                       headers=headers)
    if add_patron_result.status_code < 399:
        temp_card_number = find_card_number(add_patron_result.text)
        if temp_card_number is not None:
            con = sqlite3.connect(DB_PATH)
            cur = con.cursor()
            form['temp_card_number'] = temp_card_number
            try:
                cur.execute("""INSERT INTO LibraryCardRequest 
                           (email, temp_number) 
                    VALUES (?,?);""", (email_hash, temp_card_number,))
            except sqlite3.IntegrityError:
                pass
            
            con.commit()
            cur.close()
            con.close()
            if not pin_reset(temp_card_number):
                return "Failed to reset {}".format(temp_card_number)
            return temp_card_number
        else:
            return None
    else:
        None

def db_email_check(email_value=None):
    """Tests to see if the database already has the supplied email address

    args:
        email_value: the email address to search for
    """
    return_val = False
    if email_value and DUPLICATE_EMAIL_CHECK:
        email_hash = sha512(email_value.lower().strip().encode()).hexdigest()
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        found = bool(cur.execute("""SELECT count(*) FROM LibraryCardRequest
                WHERE email=?""", (email_hash,)).fetchone()[0])
        if found:
            return_val = True
        cur.close()
        con.close()
    return return_val

def validate_form(form):
    """validates the form data before saving

    Args:
        form: post form data

    Returns:
        dict: {valid: bool, errors: []}
    """
    errors = []
    valid_email = email_check(email=form.get('g587-email'),debug=False)
    if isinstance(valid_email, str) or (isinstance(valid_email, bool) and not valid_email):
        errors.append({"field": "g587-email",
                       "valid": False,
                       "message": valid_email})
    valid = True
    valid_postal = postal_code(zipcode=form.get('g587-zipcode'),
                               debug=False)
    if not valid_postal['valid']:
        valid_postal['field'] = "g587-zipcode"
        errors.append(valid_postal)
    valid = True
    try:
        py_date = date_parse(form.get('g587-birthday'))
        form['g587-birthday'] = py_date.strftime('%m/%d/%Y')
    except:
        errors.append({"field":"g587-birthday", 
                       "valid":False,
                       "message":"Invalid date format"})
    if len(errors) > 0:
        valid = False
    return {"valid":valid, "errors":errors, "form":form}

def email_check(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    # test to see if the function is being called by a request

    email_value = kwargs.get("email","").lower().strip()
    debug_on = kwargs.get("debug",False)
    is_valid = validate_email(email_value)
    if not is_valid:
        valid = False
        message = "Enter a valid email address"
    elif db_email_check(email_value):
        valid = False
        message = "Email has already been registered"
    else:
        valid = True
        message = True
    rtn_msg = {"valid":valid, "message":message}
    rtn_msg = message
    if debug_on:
        email_check = db_email_check(email_value)
        rtn_msg["debug"] = {
                               "email":email_value,
                               "validate_email": is_valid,
                               "db_email_check": email_check
                           }
    return rtn_msg

@app.route("/email_check")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_email_check(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    rtn_msg = email_check(email=request.args.get("g587-email","").lower(),
                          debug=request.args.get("debug",False))
    return jsonify(rtn_msg)

def postal_code(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """

    postal_value = kwargs.get("zipcode","")
    debug_on = kwargs.get("debug",False)
    valid = False
    message = "Enter all 5 digits"
    data = []
    if len(postal_value) == 5:
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        codes = cur.execute("SELECT * FROM postalcodes WHERE postal_code = ?",
                            (postal_value,)).fetchall()
        if len(codes) > 0:
            valid = True
            data = [dict(ix) for ix in codes]
            message = ""
        else:
            message = "Enter a valid US postal code"
    rtn_msg = {"valid":valid, 
               "message":message,
               "data":data}
    if debug_on:
        email_check = db_email_check(email_value)
        rtn_msg["debug"] = {
                               "postal_code":postal_value
                           }
    return rtn_msg

@app.route("/postal_code")
@crossdomain(origin=CROSS_DOMAIN_SITE)
def request_postal_code(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    rtn_msg = postal_code(zipcode=request.args.get("g587-zipcode",""),
                          debug=request.args.get("debug",False))
    return jsonify(rtn_msg)

@app.route("/", methods=["POST"])
@crossdomain(origin=CROSS_DOMAIN_SITE)
def index():
    """Default view for handling post submissions from a posted form"""
    setup_db() 
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
        #return redirect(request.referrer, code=304)
        return jsonify(valid_form)
        
@app.route("/test_form", methods=['GET', 'POST'])
def test_form():
    form_path = os.path.join(CURRENT_DIR,"wordpress","currentform.txt")
    html = ""
    with open(form_path, "r") as form_file:
        html = form_file.read()
    return html.replace("104.131.189.93", "localhost")

if __name__ == '__main__':
    print("Starting Chapel Hills Patron Registration")
    setup_db()
    app.run(host='0.0.0.0', port=4000, debug=True)
