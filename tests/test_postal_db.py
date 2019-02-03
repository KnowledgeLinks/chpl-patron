import unittest
from chplpatron import postaldb

from chplpatron.exceptions import *


class TestPostalCodeDb(unittest.TestCase):

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
            "street": "500 smith level rd appt e-21",
            # "street": "500 smith level rd",
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
        locale_info = postaldb.get_postal_code(postal_code)[0]
        self.assertEqual(locale_info['postal_code'], postal_code)
        self.assertEqual(locale_info['city'], 'Alexandria')
        self.assertEqual(locale_info['state'], 'Virginia')
        self.assertRaises(InvalidPostalCode,
                          postaldb.get_postal_code,
                          '1fsgf2')

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
