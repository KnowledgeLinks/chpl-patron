import unittest
from chplpatron import geosearch

from chplpatron.exceptions import *


class TestGeoSearch(unittest.TestCase):

    def setUp(self):
        self.valid_address = {'street': '100 Library Drive',
                              'city': 'Chapel Hill',
                              'state': 'NC',
                              'postal_code': '27514',
                              'x': -79.03561696892486,
                              'y': 35.93231469995396}

        self.out_boundary_address = {'street': '101 Independence Ave SE',
                                     'city': 'Washington',
                                     'state': 'DC',
                                     'postal_code': '20540',
                                     'x': -77.0047245,
                                     'y': 38.887101}

        self.test_address = {
            "city": "Carrboro",
            "street": "500 smith level rd",
            "state": "NC",
            "postal_code": "27510",
        }
        self.test_address2 = {

            "state": "NC",
            "postal_code": "27514",
            "street": "100 library dr"
        }

    def test_get_locale_from_postal_code(self):
        # self.assertGreater(len(geosearch.get_locale_from_postal_code(81137)),
        #                    1)
        postal_code = '22308'
        locale_info = geosearch.get_postal_code(postal_code)[0]
        self.assertEqual(locale_info['postal_code'], postal_code)
        self.assertEqual(locale_info['city'], 'Alexandria')
        self.assertEqual(locale_info['state'], 'Virginia')
        self.assertRaises(InvalidPostalCode,
                          geosearch.get_postal_code,
                          '1fsgf2')

    def test_get_geocoords_from_address(self):
        geo_coords = geosearch.get_geo_coords(self.valid_address)
        self.assertEqual(self.valid_address['x'], geo_coords['x'])
        self.assertEqual(self.valid_address['y'], geo_coords['y'])

    def test_boundary_check(self):
        self.assertTrue(geosearch.check_boundary_coords(self.valid_address))
        self.assertFalse(geosearch.check_boundary_coords(
                self.out_boundary_address))

    def test_check_address(self):

        # valid = self.valid_address.copy()
        # del valid['x']
        # del valid['y']
        # self.assertTrue(geosearch.check_address(**valid))
        # self.assertFalse(geosearch.check_address(**self.out_boundary_address))
        print(geosearch.check_address(**self.test_address))
        print(geosearch.check_address(**self.test_address2))

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
