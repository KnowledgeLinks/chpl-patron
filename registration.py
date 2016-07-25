"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson"

import csv
import os
import re
import requests
import smtplib
import sqlite3
from email.mime.text import MIMEText
from flask import Flask, request, jsonify, abort

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile("config.py")

CURRENT_DIR = os.path.abspath(os.curdir)
DB_PATH = app.config.get("DB_PATH")
if DB_PATH is None:
    DB_PATH = os.path.join(
        CURRENT_DIR,
        "card-requests.sqlite")
    
def add_contact(form, con, patron_id):
    """Creates rows in Email and Telephone Tables

    Args:
        form (request.form): Flask request form
        con (sqlite3.connection): Database Connection
        patron_id(int): Integer 
    """
    email = form.get("g587-email")
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
    zip_code = form.get("g587-zipcode")
    cur = con.cursor()
    cur.execute("""SELECT id FROM Location
WHERE address=? AND zip_code=?""",
        (address, zip_code))
    result = cur.fetchone()
    if result:
        location_id = result[0]
    else:
        cur.execute("""INSERT INTO Location (address, zip_code)
VALUES (?,?);""",
            (address, zip_code))
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


def generate_csv():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""SELECT DISTINCT LibraryCardRequest.date, Patron.first_name, 
Patron.last_name, Patron.birth_day, Location.address, Location.zip_code, 
Email.address, Telephone.number 
FROM LibraryCardRequest, Patron, Location, Email, Telephone 
WHERE LibraryCardRequest.patron = Patron.id AND 
LibraryCardRequest.location = Location.id AND 
Email.patron = Patron.id AND 
Telephone.patron = Patron.id""")
    results = cur.fetchall()

def register_patron(registration_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""SELECT DISTINCT Patron.first_name, Patron.last_name, Patron.birth_day,
Location.address, Location.zip_code, Telephone.number, Email.address
FROM LibraryCardRequest, Patron, Location, Email, Telephone
WHERE LibraryCardRequest.id=? AND 
LibraryCardRequest.patron = Patron.id AND
LibraryCardRequest.location = Location.id AND
Email.patron = Patron.id AND
Telephone.patron = Patron.id""", (registration_id,))
    result = cur.fetchone()
    data = {
        "nname": "{} {}".format(result[0], result[1]),
        "F051birthdate": result[2],
        "full_aaddress": "{}, {}".format(result[3], result[4]),
        "zemailaddr": result[5],
        "tphone1": result[6]}
    add_patron_result = requests.post(app.config.get('SIERRA_URL'),
        data=data)
    if add_patron_result.status_code < 399:
        temp_card_number = find_card_number(add_patron_result.text)
        print(add_patron_result.text)
        print("Temporary card number is {}".format(temp_card_number))
        if temp_card_number is not None:
            cur.execute("""UPDATE LibraryCardRequest SET temp_number=? 
WHERE id=?""", (temp_card_number, registration_id))
            con.commit()
            cur.close()
            con.close()
            result.append(temp_card_number)
            email_notification(result)
            return True
    cur.close()
    con.close()
    return False
        

@app.route("/report")
def report():
    return "IN REPORT"

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
    if register_patron(card_request_id) is True:
        #! Should redirect to WP success page
        return jsonify({"Patron": card_request_id})
    abort(505)
        
    

if __name__ == '__main__':
    print("Starting Chapel Hills Patron Registration")
    app.run(host='0.0.0.0', port=4000, debug=True)
