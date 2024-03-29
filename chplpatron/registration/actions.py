import requests
import smtplib
import datetime

from email.mime.text import MIMEText
from .utilities import (Flds,
                        form_to_api)
from chplpatron import sierra
from chplpatron import trackingdb


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


def register_patron(form, location, boundary):
    """
    send the patron data to sierra and adds a hash of the registered email
    to the local sqlite db
    :param form: the form data
    :param location: 'internal' or 'external' registration source
    :param boundary: True or False whether address is within boundary
    :return: the temp_card_number or None if not successful
    """
    patron = form_to_api(form)
    var_field = sierra.VarField()
    var_field.fieldTag = "m"
    var_field.content = boundary['message']
    patron.varFields = var_field
    patron.expirationDate = (datetime.datetime.now() + datetime.timedelta(30))\
        .strftime("%Y-%m-%d")
    patron.pMessage = 'f'
    result = sierra.create_patron(patron)

    if result:
        temp_card_number = result
        if temp_card_number is not None:
            trackingdb.add_registration(temp_card_number,
                                        form.get(Flds.email.frm),
                                        location,
                                        boundary['valid'])
            # if not pin_reset(temp_card_number):
            #     return "Failed to reset {}".format(temp_card_number)
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


def email_notification(form, from_fld, to_fld, boundary_status):
    """
    Sends an email notification of new card request
    :param form: form date
    :param from_fld: from email address
    :param to_fld:  to email address
    :return:
    """
    email = form.get(Flds.email.frm).lower().strip()
    body = ("New Library Card Request\n"
            "Name: {0} {1}\n"
            "Birthday: {2}\n"
            "Address: {3}, {4}, {5} {6}\n"
            "\t[{10}]\n"
            "Phone number: {7}\n"
            "Email: {8}\n"
            "Temporary Library Card Number: {9}\n")\
        .format(form.get(Flds.first_name.frm),
                form.get(Flds.last_name.frm),
                form.get(Flds.birthday.frm),
                form.get(Flds.street.frm),
                form.get(Flds.city.frm),
                form.get(Flds.state.frm),
                form.get(Flds.postal_code.frm),
                form.get(Flds.phone.frm),
                email,
                form.get("temp_card_number"),
                boundary_status)
    msg = MIMEText(body)
    msg['Subject'] = "New Card Request"
    msg['From'] = from_fld
    msg['To'] = ','.join(to_fld)
    msg['To'] += ",{}".format(email)
    mail_server = smtplib.SMTP('localhost')
    mail_server.send_message(msg)
    mail_server.quit()
