from validate_email import validate_email
from dateutil.parser import parse as date_parse

from chplpatron import geosearch
from chplpatron import sierra
from chplpatron.exceptions import *

from .messages import InvalidMsgs


def validate_form(form):
    """validates the form data before saving

    Args:
        form: post form data

    Returns:
        dict: {valid: bool, errors: []}
    """
    errors = []

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
        errors.append({"field": "g587-birthday",
                       "valid": False,
                       "message": "Invalid date format"})
    if len(errors) > 0:
        valid = False
    return {"valid": valid, "errors": errors, "form": form}


def email_check(**kwargs):
    """
    Checks to see if the email address as has already been registered

        request args:
            g587-email: the email address to check
    """
    # test to see if the function is being called by a request

    email_value = kwargs.get("email", "").lower().strip()
    debug_on = kwargs.get("debug", False)
    valid = True
    message = True
    if not validate_email(email_value):
        valid = False
        message = "Enter a valid email address"
    else:
        try:
            sierra.check_email(email_value)
        except RegisteredEmailError:
            valid = False
            message = InvalidMsgs.email_reg.value

    rtn_msg = {"valid": valid, "message": message}

    if debug_on:
        try:
            db_email_check = sierra.check_email(email_value)
        except RegisteredEmailError:
            db_email_check = False
        rtn_msg["debug"] = {
                               "email": email_value,
                               "validate_email": validate_email(email_value),
                               "db_email_check": db_email_check
                           }
    return rtn_msg


def postal_code(**kwargs):
    """ Checks the postal code

        request args:
            zipcode: the postal code to check
    """

    postal_value = kwargs.get("zipcode", "")
    debug_on = kwargs.get("debug", False)
    valid = False
    message = "Enter all 5 digits"
    data = []
    if len(postal_value) == 5:
        try:
            locations = geosearch.get_postal_code(postal_value)
            valid = True
            data = [ix.get('city') for ix in locations]
            message = ""
        except InvalidPostalCode:
            message = InvalidMsgs.invalid_postal_code.value
    rtn_msg = {"valid": valid,
               "message": message,
               "data": data}
    if debug_on:
        rtn_msg["debug"] = {
                               "postal_code": postal_value
                           }
    return rtn_msg


def boundary_check(**kwargs):
    within = geosearch.check_address(**kwargs)
    message = ""
    if not within:
        message = InvalidMsgs.not_within_boundary.value
    rtn_msg = {"valid": within,
               "message": message}
    return rtn_msg
