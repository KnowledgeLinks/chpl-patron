import re

from validate_email import validate_email
from dateutil.parser import parse as date_parse

from requests.exceptions import ConnectionError
from chplpatron import (geosearch,
                        sierra,
                        postaldb)

from chplpatron.exceptions import *

from .messages import InvalidMsgs
from .utilities import Flds


def validate_form(form):
    """validates the form data before saving

    Args:
        form: post form data

    Returns:
        dict: {valid: bool, errors: []}
    """
    errors = []

    valid = True
    valid_postal = postal_code(zipcode=form.get(Flds.postal_code.frm),
                               debug=False)
    if not valid_postal['valid']:
        valid_postal['field'] = Flds.postal_code.frm
        errors.append(valid_postal)
    else:
        if form.get(Flds.city.frm) in [None, ""]:
            form[Flds.city.frm] = valid_postal['data']['city'][0]
        if form.get(Flds.state.frm) in [None, ""]:
            form[Flds.state.frm] = valid_postal['data']['state']
    try:
        py_date = date_parse(form.get(Flds.birthday.frm))
        form[Flds.birthday.frm] = py_date.strftime('%m/%d/%Y')
        if py_date.year < 1900:
            errors.append({"field": Flds.birthday.frm,
                           "valid": False,
                           "message": "Birth year less than 1900 is not allowed."})
    except:
        errors.append({"field": Flds.birthday.frm,
                       "valid": False,
                       "message": "Invalid date format"})
    val_password = validate_password(form.get(Flds.password.frm))
    if not val_password['valid']:
        val_password['field'] = Flds.password.frm
        errors.append(val_password)
    val_email = email_check(email=form.get(Flds.email.frm))
    if not val_email['valid']:
        val_email['field'] = Flds.email.frm
        errors.append(val_email)
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
    # if valid:
    #     rtn_msg = True
    # else:
    #     rtn_msg = message
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


def postal_code(zipcode, **kwargs):
    """ Checks the postal code

        request args:
            zipcode: the postal code to check
    """

    postal_value = zipcode
    debug_on = kwargs.get("debug", False)
    valid = False
    message = "Enter all 5 digits"
    data = {"city": [], "state": ""}
    if len(postal_value) > 5:
        postal_value = postal_value[:5]
    if len(postal_value) == 5:
        try:
            locations = geosearch.get_postal_code(postal_value)
            valid = True
            data['city'] = [ix.get('city') for ix in locations]
            data['state'] = [ix.get("state") for ix in locations][0]
            message = ""
        except InvalidPostalCode:
            message = InvalidMsgs.invalid_postal_code.value
        except (AttributeError, ConnectionError):
            try:
                locations = postaldb.get_postal_code(postal_value)
                valid = True
                data['city'] = [ix.get('city') for ix in locations]
                data['state'] = [ix.get("state") for ix in locations][0]
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


REQ_BOUNDARY = {'street', 'city', 'state', 'postal_code'}


def boundary_check(**kwargs):
    if REQ_BOUNDARY.difference(set(kwargs.keys())):
        return {"valid": False,
                "message": "Missing fields {}"
                .format(", ".join(REQ_BOUNDARY.difference(set(kwargs.keys()))))}
    try:
        within = geosearch.check_address(**kwargs)
    except:
        return {"valid": None,
                "message": InvalidMsgs.not_able_to_check_boundary.value}
    message = "The address is within the library boundary"
    if not within:
        message = InvalidMsgs.not_within_boundary.value
    rtn_msg = {"valid": within,
               "message": message}
    return rtn_msg


def validate_password(password):
    """
    validates if a password is acceptable
    :param password: the password to validate
    :return:
    """
    if re.findall(r'[^a-zA-Z0-9]', password) or len(password) > 30:
        return {"valid": False,
                "message": InvalidMsgs.password.value}
    return {"valid": True,
            "message": ""}

