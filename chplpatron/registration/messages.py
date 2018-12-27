from enum import Enum


class InvalidMsgs(Enum):
    email_reg = "Email has already been registered."
    invalid_postal_code = "Enter a valid US postal code."
    not_within_boundary = "Address is not within the Chapel Hill Boundary"
