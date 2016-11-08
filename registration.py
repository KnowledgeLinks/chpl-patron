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
from flask import Flask, request, jsonify, abort, redirect
from validate_email import validate_email
from hashlib import sha512
from dateutil.parser import parse as date_parse

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile("config.py")

CURRENT_DIR = os.path.abspath(os.curdir)
DB_PATH = app.config.get("DB_PATH")
if DB_PATH is None:
    DB_PATH = os.path.join(
        CURRENT_DIR,
        "card-requests.sqlite")

def setup_db():
    """ checks to see if the database is setup and sets if up if it doesn't"""

    if not os.path.exists(DB_PATH):
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        with open(os.path.join(CURRENT_DIR, "db-schema.sql")) as script_fo:
            script = script_fo.read()
            cur.executescript(script)
        cur.close()
        con.close()
        setup_postalcodes()

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
        print("Setting Postal Codes")
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
    email = form.get("g587-email","").lower()
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

def register_patron(form):
    """send the patron data to iii and adds a hash of the registered email
    to the local sqlite db

    Args:
        form
    """
    data =  {
                "nfirst": form.get("g587-firstname"), 
                "nlast": form.get("g587-lastname"),
                "F051birthdate": form.get("g587-birthday"),
                "stre_aaddress": form.get("g587-address"),
                "city_aaddress": form.get("g587-city"),
                "stat_aaddress": form.get("g587-state"),
                "post_aaddress": form.get("g587-zipcode"),
                "tphone1": form.get("g587-telephone"),
                "zemailaddr": form.get("g587-email","").lower()
            }

    email_hash = sha512(form.get("g587-email","").lower().encode()).hexdigest()   
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
            cur.execute("""INSERT INTO LibraryCardRequest 
                           (email, temp_number) 
                           VALUES (?,?);""", (email_hash, temp_card_number,))
            con.commit()
            cur.close()
            con.close()
            email_notification(form)
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
    if email_value:
        email_hash = sha512(email_value.lower().encode()).hexdigest()
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
    if isinstance(valid_email, bool) and not valid_email:
        valid_email['field'] = "g587-email"
        errors.append(valid_email)
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

@app.route("/report")
def report():
    return "IN REPORT"

@app.route("/email_check")
def email_check(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    # test to see if the function is being called by a request
    return_dict = False
    if kwargs.get("email"):
        return_dict = True

    email_value = kwargs.get("email",
                             request.args.get("g587-email","")).lower()
    debug_on = kwargs.get("debug",request.args.get("debug",False))
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
    if return_dict:
        return rtn_msg
    else:
        return jsonify(rtn_msg)

@app.route("/postal_code")
def postal_code(**kwargs):
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    return_dict = False
    if kwargs.get("zipcode"):
        return_dict = True

    postal_value = kwargs.get("zipcode",
                              request.args.get("g587-zipcode",""))
    debug_on = kwargs.get("debug",request.args.get("debug",False))
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
    if return_dict:
        return rtn_msg
    else:
        return jsonify(rtn_msg)

@app.route("/", methods=["POST"])
def index():
    """Default view for handling post submissions from a posted form"""
    setup_db() 
    if not request.method.startswith("POST"):
        return "Method not supported"
    form = request.form.to_dict()
    print(form)
    valid_form = validate_form(form)
    print(valid_form['form'])
    if valid_form['valid']:
        temp_card_number = register_patron(valid_form['form'])
        if temp_card_number is not None:
            return jsonify({"valid": True,
                            "url": "{}?number={}".format(
                                  app.config.get("SUCCESS_URI"),
                                  temp_card_number)})
        else:
            return jsonify({"valid": True,
                            "url": "{}?error={}".format(
                                    app.conf.get("ERROR_URI"),
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
