"""
State lookup module for converting between State abbreviations and full names

"""

from chplexceptions import InvalidState

__DATA__ = [
    ('Alabama', 'AL'),
    ('Alaska', 'AK'),
    ('Arizona', 'AZ'),
    ('Arkansas', 'AR'),
    ('California', 'CA'),
    ('Colorado', 'CO'),
    ('Connecticut', 'CT'),
    ('Delaware', 'DE'),
    ('Florida', 'FL'),
    ('Georgia', 'GA'),
    ('Hawaii', 'HI'),
    ('Idaho', 'ID'),
    ('Illinois', 'IL'),
    ('Indiana', 'IN'),
    ('Iowa', 'IA'),
    ('Kansas', 'KS'),
    ('Kentucky', 'KY'),
    ('Louisiana', 'LA'),
    ('Maine', 'ME'),
    ('Maryland', 'MD'),
    ('Massachusetts', 'MA'),
    ('Michigan', 'MI'),
    ('Minnesota', 'MN'),
    ('Mississippi', 'MS'),
    ('Missouri', 'MO'),
    ('Montana', 'MT'),
    ('Nebraska', 'NE'),
    ('Nevada', 'NV'),
    ('New Hampshire', 'NH'),
    ('New Jersey', 'NJ'),
    ('New Mexico', 'NM'),
    ('New York', 'NY'),
    ('North Carolina', 'NC'),
    ('North Dakota', 'ND'),
    ('Ohio', 'OH'),
    ('Oklahoma', 'OK'),
    ('Oregon', 'OR'),
    ('Pennsylvania', 'PA'),
    ('Rhode Island', 'RI'),
    ('South Carolina', 'SC'),
    ('South Dakota', 'SD'),
    ('Tennessee', 'TN'),
    ('Texas', 'TX'),
    ('Utah', 'UT'),
    ('Vermont', 'VT'),
    ('Virginia', 'VA'),
    ('Washington', 'WA'),
    ('West Virginia', 'WV'),
    ('Wisconsin', 'WI'),
    ('Wyoming', 'WY'),
    ('American Samoa', 'AS'),
    ('District of Columbia', 'DC'),
    ('Federated States of Micronesia', 'FM'),
    ('Guam', 'GU'),
    ('Marshall Islands', 'MH'),
    ('Northern Mariana Islands', 'MP'),
    ('Palau', 'PW'),
    ('Puerto Rico', 'PR'),
    ('Virgin Islands', 'VI'),
    ('Armed Forces Africa', 'AE'),
    ('Armed Forces Americas', 'AA'),
    ('Armed Forces Canada', 'AE'),
    ('Armed Forces Europe', 'AE'),
    ('Armed Forces Middle East', 'AE'),
    ('Armed Forces Pacific', 'AP')
]
# dict with lowercased state fullname key
__LOWER_FULL__ = {item[0].lower(): item[1] for item in __DATA__}
# dict with lowercased state abbreviation key
__LOWER_ABBR__ = {item[1].lower(): item[0] for item in __DATA__}


def get_name(value):
    """
    Get the state name for the supplied value
    :param value: abbreviation or full name
    :return: String of full state name
    """
    if len(value) == 2:
        try:
            return __LOWER_ABBR__[value.lower()]
        except KeyError:
            raise InvalidState(value)
    try:
        return __LOWER_ABBR__[__LOWER_FULL__[value.lower().strip()].lower()]
    except KeyError:
        raise InvalidState(value)


def get_abbreviation(value):
    """
    Get the state abbreviation for the supplied value
    :param value: abbreviation or full name
    :return: String of full state name
    """
    if len(value) == 2:
        try:
            return __LOWER_FULL__[__LOWER_ABBR__[value.lower().strip()].lower()]
        except KeyError:
            raise InvalidState(value)
    try:
        return  __LOWER_FULL__[value.lower()]
    except KeyError:
        raise InvalidState(value)


def is_state(value):
    """
    tests to see if the value is a state
    :param value: abbreviation or full name
    :return: true if the value is a state -- false if it is not a state
    """

    try:
        return len(get_abbreviation(value)) > 0
    except InvalidState:
        return False
