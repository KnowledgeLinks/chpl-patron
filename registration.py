"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson, Mike Stabile"

import csv
import os
import re
import requests
import smtplib
import sqlite3
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, abort, redirect
from validate_email import validate_email

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile("config.py")

CURRENT_DIR = os.path.abspath(os.curdir)
DB_PATH = app.config.get("DB_PATH")
if DB_PATH is None:
    DB_PATH = os.path.join(
        CURRENT_DIR,
        "card-requests.sqlite")

def setup_postalcodes(con):
    """Setups up the database with postal codes if not already added to the
    the database

    Args:
        con (sqlite3.connection): Database Connection
    """
    postalcodes_setup = False

    # test to see if the table exists
    qry = """SELECT name 
FROM sqlite_master 
WHERE type='table' AND name='postalcodes';"""

    cur = con.cursor()
    cur.execute(qry)
    tbl_exists = False
    for row in cur.fetchall():
        exists = True
        break

    # get the row count... if the row count is small reload the table
    if tbl_exists:
        count = cur.execute("SELECT count(*) FROM postalcodes;").fetchone()
        if count > 1000:
            postalcodes_setup = True

    if not postalcodes_setup:
        delete_tbl_sql = "DROP TABLE IF EXISTS postalcodes"
        create_tbl_sql = """CREATE TABLE IF NOT EXISTS postalcodes (
 zip_code text PRIMARY KEY,
 city text NOT NULL
 state_long text NOT NULL,
 state_short text,
 lat as text,
 long as text
) WITHOUT ROWID;"""

        cur.execute(delete_tbl_sql)
        cur.execute(create_tbl_sql)
        # read the datafile and add to the database
        with open(os.path.join(CURRENT_DIR,"postalcodes","US.txt","r")) as data:
            pcodes = list(csv.reader(data, delimiter='\t'))
            for ln in pcodes:
                cur.execute("INSERT INTO postalcodes (%s %s %s %s %s %s) %s" % 
                        ("zip_code", 
                         "city",
                         "state_long", 
                         "state_short", 
                         "lat", 
                         "long",
                         "VALUES (?,?,?,?,?,?)"),
                        (ln[1], ln[2], ln[3], ln[4], ln[7], ln[8]))

def add_contact(form, con, patron_id):
    """Creates rows in Email and Telephone Tables

    Args:
        form (request.form): Flask request form
        con (sqlite3.connection): Database Connection
        patron_id(int): Integer 
    """
    email = form.get("g587-email","").lower()
    telephone = form.get("g587-telephone")
    cur = con.cursor()
    cur.execute("INSERT INTO Email (address, patron) VALUES (?,?)",
                (email, patron_id))
    cur.execute("INSERT INTO Telephone (number, patron) VALUES (?,?)",
                (telephone, patron_id))
    con.commit()
    cur.close()


def add_location(form, con):
    """Creates row in the Location table

    Args:
        form (request.form): Flask request form
        con (sqlite3.connection): Database Connection

    Returns:
        int: Location code
    """
    cur = con.cursor()
    address = form.get("g587-address")
    city = form.get("g587-city")
    state = form.get("g587-state")
    zip_code = form.get("g587-zipcode")
    cur = con.cursor()
    cur.execute("""SELECT id FROM Location
WHERE address=? AND city=? AND state=? AND zip_code=?""",
        (address, city, state, zip_code))
    result = cur.fetchone()
    if result:
        location_id = result[0]
    else:
        cur.execute("""INSERT INTO Location (address, city, state, zip_code)
VALUES (?,?,?,?);""",
            (address, city, state, zip_code))
        con.commit()
        cur.execute("SELECT max(id) FROM Location;")
        location_id = cur.fetchone()[0]
    cur.close()
    return location_id
    

def create_patron(form, con):
    """Creates a row in the Patron table

    Args:
        form (request.form): Flask request form
        con (sqlite3.connection): Database Connection

    Returns:
        int: Existing or New Patron id
    """
    cur = con.cursor()
    first_name = form.get("g587-firstname")
    last_name = form.get("g587-lastname")
    birth_day = form.get("g587-birthday")
    cur.execute("""SELECT id FROM Patron 
WHERE first_name=? AND last_name=? AND birth_day=?;""",
        (first_name, last_name, birth_day))
    result = cur.fetchone()
    if result is not None:
        patron_id = result[0]
    else:
        cur.execute("""INSERT INTO Patron (first_name, last_name, birth_day)
VALUES(?,?,?)""",
        (first_name, last_name, birth_day))
        con.commit()
        cur.execute("""SELECT max(id) FROM Patron""")
        patron_id = cur.fetchone()[0]
    cur.close()
    return patron_id
   

def create_registration(form):
    con = sqlite3.connect(DB_PATH)
    patron_id = create_patron(form, con)
    location_id = add_location(form, con)
    add_contact(form, con, patron_id)
    cur = con.cursor()
    cur.execute("""INSERT INTO LibraryCardRequest (patron, location)
VALUES (?,?);""",
        (patron_id, location_id))
    con.commit()
    card_request_id = cur.execute(
        "SELECT max(id) FROM LibraryCardRequest;").fetchone()[0]
    cur.close()
    con.close()
    return card_request_id


def email_notification(db_result):
    """Sends an email notification of new card request

    Args:
        db_result(list): List of data from the database query
    """
    body = """New Library Card Request
Name: {0} {1}
Birthday: {2}
Address: {3}
Zip Code: {4}
Phone number: {5}
Email: {6}
Temporary Library Card Number: {7}
""".format(*db_result)
    msg = MIMEText(body)
    msg['Subject'] = "New Card Request"
    msg['From'] = app.config["EMAIL_SENDER"] 
    msg['To'] = ','.join(app.config["EMAIL_RECIPIENTS"])
    msg['To'] += ",{}".format(db_result[6])
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


def register_patron(registration_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""SELECT DISTINCT Patron.first_name, Patron.last_name, Patron.birth_day,
Location.address, Location.city, Location.state, Location.zip_code, Telephone.number, Email.address
FROM LibraryCardRequest, Patron, Location, Email, Telephone
WHERE LibraryCardRequest.id=? AND 
LibraryCardRequest.patron = Patron.id AND
LibraryCardRequest.location = Location.id AND
Email.patron = Patron.id AND
Telephone.patron = Patron.id""", (registration_id,))
    result = list(cur.fetchone())
    data = {
        "nfirst": result[0], 
        "nlast": result[1],
        "F051birthdate": result[2],
        "stre_aaddress": result[3],
        "city_aaddress": result[4],
        "stat_aaddress": result[5],
        "post_aaddress": result[6],
        "tphone1": result[7],
        "zemailaddr": result[8].lower()}
    add_patron_result = requests.post(app.config.get('SIERRA_URL'),
        data=data,
        headers={"Cookie": 'SESSION_LANGUAGE=eng; SESSION_SCOPE=0; III_EXPT_FILE=aa31292'})
    if add_patron_result.status_code < 399:
        temp_card_number = find_card_number(add_patron_result.text)
        if temp_card_number is not None:
            cur.execute("""UPDATE LibraryCardRequest SET temp_number=? 
WHERE id=?""", (temp_card_number, registration_id))
            con.commit()
            cur.close()
            con.close()
            result.append(temp_card_number)
            email_notification(result)
            return temp_card_number
    cur.close()
    con.close()

def db_email_check(email_value=None):
    """Tests to see if the database already has the supplied email address

    args:
        email_value: the email address to search for
    """
    return_val = False
    if email_value:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("""SELECT DISTINCT Email.address FROM Email
WHERE Email.address=? """, (email_value.lower()))
        result = list(cur.fetchone())
        if result[0]:
            return_val = True
        cur.close()
        con.close()
    return return_val

def verify_address(form):
    """ calls the lob.com address verification api
    https://lob.com/docs#verixfy_create
    """
    result = requests.post(url="https://api.lob.com/v1/verify",
            data={"address_line1":form.get("g587-address"),
                 "address_city":form.get("g587-city"),
                 "address_state":form.get("g587-state"),
                 "address_zip":form.get("g587-zipcode")},
            headers={"user": test_0dc8d51e0acffcb1880e0f19c79b2f5b0cc})

@app.route("/report")
def report():
    return "IN REPORT"

@app.route("/email_check")
def email_check():
    """ Checks to see if the email address as has already been registered 

        request args:
            g587-email: the email address to check
    """
    email_value = request.args.get("g587-email","").lower()
    debug_on = reguest.args.get("debug",False)
    is_valid = validate_email(email_value)
    debug_data = 
    if not is_valid:
        valid = False
        message = "Enter a valid email address"
    elif db_email_check(email_value):
        valid = False
        message = "Email has already been registered"
    else:
        valid = True
        message = None
    rtn_msg = {"valid":valid, "message":message}
    if debug_on:
        email_check = db_email_check(email_value)
        rtn_msg["debug"] = {
                               "email":email_value,
                               "validate_email": is_valid
                               "db_email_check": email_check
                           }
    return jsonify(rtn_msg)


@app.route("/", methods=["POST"])
def index():
    """Default view for handling post submissions from a posted form"""
    if not os.path.exists(DB_PATH):
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        with open(os.path.join(CURRENT_DIR, "db-schema.sql")) as script_fo:
            script = script_fo.read()
            cur.executescript(script)
        cur.close()
        con.close()  
    if not request.method.startswith("POST"):
        return "Method not support"
    card_request_id = create_registration(request.form)
    temp_card_number = register_patron(card_request_id)
    if temp_card_number is not None:
        return redirect("{}?number={}".format(
            app.config.get("SUCCESS_URI"),
            temp_card_number))
    else:
        return redirect("{}?error={}".format(
            app.conf.get("ERROR_URI"),
            "Failed to register Patron"))
        
    

if __name__ == '__main__':
    print("Starting Chapel Hills Patron Registration")
    setup_postalcode
    app.run(host='0.0.0.0', port=4000, debug=True)