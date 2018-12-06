import requests
import smtplib
import sqlite3

from email.mime.text import MIMEText
from hashlib import sha512
from .utilities import FldAssoc


def pin_reset(temp_pin, url):
    """
    Takes a temporary pin and calls III's PIN reset form and returns message
    if successful.

    Args:
        temp_pin(str): Temporary card pin

    Returns:
        string: PIN Reset
    """
    pin_reset_result = requests.post(url, data={"code": temp_pin})
    if pin_reset_result.status_code > 399:
        return False
    return True


def register_patron(form):
    """
    send the patron data to iii and adds a hash of the registered email
    to the local sqlite db

    Args:
        form
    """
    addr_string = form.get(FldAssoc.street.value.frm)
    addr_string2 = "{}, {} {}".format(
        form.get(FldAssoc.city.value.frm),
        form.get(FldAssoc.state.value.frm),
        form.get(FldAssoc.postal_code.value.frm))
    data = {
        FldAssoc.last_name.value.api.name: [
            "{}, {}".format(form.get(FldAssoc.last_name.value.frm),
                            form.get(FldAssoc.first_name.value.frm))],
        FldAssoc.birthday.value.api.name: form.get(FldAssoc.birthday.value.frm),
        "full_aaddress": [addr_string, addr_string2],
        "tphone1": form.get("g587-telephone"),
        "zemailaddr": form.get("g587-email", "").lower().strip()
    }

    email_hash = sha512(
        form.get("g587-email", "").lower().strip().encode()).hexdigest()
    headers = {
        "Cookie": 'SESSION_LANGUAGE=eng; SESSION_SCOPE=0; III_EXPT_FILE=aa31292'}
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


def find_card_number(patron):
    """
    Gets the card number from the patron record
    :param patron: patron record dictionary
    :return: card_number
    """
    return patron.get("id")


def email_notification(form, from_fld, to_fld):
    """Sends an email notification of new card request

    Args:
        db_result(list): List of data from the database query
    """
    email = form.get("g587-email","").lower().strip()
    body = ("New Library Card Request\n"
            "Name: {0} {1}\n"
            "Birthday: {2}\n"
            "Address: {3}, {4}, {5} {6}\n"
            "Phone number: {7}\n"
            "Email: {8}\n"
            "Temporary Library Card Number: {9}\n")\
        .format(form.get("g587-firstname"),
                form.get("g587-lastname"),
                form.get("g587-birthday"),
                form.get("g587-address"),
                form.get("g587-city"),
                form.get("g587-state"),
                form.get("g587-zipcode"),
                form.get("g587-telephone"),
                email,
                form.get("temp_card_number"))
    msg = MIMEText(body)
    msg['Subject'] = "New Card Request"
    msg['From'] = from_fld
    msg['To'] = ','.join(to_fld)
    msg['To'] += ",{}".format(email)
    mail_server = smtplib.SMTP('localhost')
    mail_server.send_message(msg)
    mail_server.quit()
