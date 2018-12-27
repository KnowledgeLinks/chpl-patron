"""
Module for validating address information for a patron
"""
import requests

from chplpatron.exceptions import *

POSTAL_CODE_CHECK_URL = ("https://geocode.arcgis.com/arcgis/rest/services/"
                         "World/GeocodeServer/find?text={}&f=pjson")

# POSTAL_CODE_CHECK_URL = ("http://production.shippingapis.com/ShippingAPI.dll"
#                          "?API=CityStateLookup&XML=<CityStateLookupRequest%20"
#                          "USERID=\"{user_id}\">"
#                          "<ZipCode ID= \"0\">"
#                          "<Zip5>{postal_code}</Zip5>"
#                          "</ZipCode></CityStateLookupRequest>").format(
#                          user_id=instance.USPS_USER_ID,
#                          postal_code="{}")

POSTAL_KEYS = ['postal_code', 'city', 'state']

GEO_FROM_ADDRESS_URL = ("https://geocode.arcgis.com/arcgis/rest/services/"
                        "World/GeocodeServer/find?text="
                        "{street}%2C+{city}%2C+{state}+{postal_code}"  # address
                        "&f=pjson")

BOUNDARY_CHECK_URL = ("https://gisweb.townofchapelhill.org/arcgis/rest/"
                      "services/MapServices/ToCH_OrangeCo_CombinedLimits/"
                      "MapServer/0/query?geometry="
                      "{x}%2C{y}"  # x y variables
                      "&geometryType=esriGeometryPoint&inSR=4326&"
                      "spatialRel=esriSpatialRelWithin&returnGeometry=false"
                      "&outSR=102100&returnCountOnly=true&f=json")


def get_postal_code(postal_code):
    """
    Queries the ARCGIS server for locale information of a zipcode

    :param postal_code: 5 digit postal code to search
    :return: response json
    """
    url = POSTAL_CODE_CHECK_URL.format(postal_code)
    response = requests.get(url)
    if response.status_code < 399:
        locs = [dict(zip(POSTAL_KEYS,
                         [part.strip()
                          for part in loc.get('name', ",,,").split(",")]))
                for loc in response.json().get('locations', [{}])]
        if len(locs) > 0 and locs[0].get('city'):
            return locs
        raise InvalidPostalCode(postal_code)

    raise RemoteApiError(url, response)


def update_city(city, postal_code, **kwargs):
    locations = get_postal_code(postal_code)
    for loc in locations:
        if city.strip().lower() == loc['city'].lower():
            kwargs['city'] = loc['city']
            kwargs['postal_code'] = postal_code
            return kwargs
    raise InvalidCity(city)


def get_geo_coords(address):
    """
    Queries ARCGIS server to find lat long of the supplied address

    :param address: dict with keys ['street', 'city', 'state', 'postal_code']
    :return: dict with keys ['x', 'y']
    """

    url = GEO_FROM_ADDRESS_URL.format(**address)
    response = requests.get(url)
    if response.status_code < 399:
        address.update(response.json().get('locations', [{}])[0]
                                      .get('feature', {})
                                      .get('geometry', {'x': '', 'y': ''}))
        return address

    raise RemoteApiError(url, response)


def check_boundary_coords(coords):
    """
    Queries ARGGIS server to check if the x y coords to see if they are within
    the defined boundary

    :param coords: dict with keys ['x', 'y']
    :return: boolean 'true' = within boundary 'false' = not in boundary
    """

    url = BOUNDARY_CHECK_URL.format(**coords)
    response = requests.get(url)
    if response.status_code < 399:
        return bool(response.json().get('count', 0))

    raise RemoteApiError(url, response)


def check_address(**address):
    """
    Queries an address to see if it is a valid postal code and if it is within
    the boundary

    :param address: dict with keys ['street', 'city', 'state', 'postal_code']
    :return:
    """
    address = update_city(**address)
    address = get_geo_coords(address)
    return check_boundary_coords(address)
