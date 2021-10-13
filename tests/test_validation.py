import unittest

from chplpatron.registration import validation


class TestValidation(unittest.TestCase):
    test_email = "testemail@gmail.com"

    def setUp(self):
        pass

    def test_validate_password(self):
        self.assertTrue(validation.validate_password("adfadg987983")['valid'])
        self.assertFalse(validation.validate_password("adf%$#%3")['valid'])
        self.assertFalse(validation.validate_password("adf 3")['valid'])

    def test_valid_form(self):
        valid_form = {
            "g587-firstname": "kj",
            "g587-birthday": "01/29/01",
            "g587-telephone": "919-932-2777",
            "g587-lastname": "test",
            "g587-email": "k@j",
            # "g587-state": "NC",
            "g587-zipcode": "27514",
            "g587-address": "100 library dr",
            "g587-password": "1234qwer"
        }
        self.assertTrue(validation.validate_form(valid_form)['valid'])

    def test_invalid_form(self):
        invalid_form = {
            "g587-firstname": "kj",
            "g587-birthday": "01/29/01",
            "g587-telephone": "919-932-2777",
            "g587-lastname": "test",
            "g587-email": "k@j",
            # "g587-state": "NC",
            "g587-zipcode": "27514",
            "g587-address": "100 library dr",
            "g587-password": "1234qwer"
        }
        self.assertTrue(validation.validate_form(invalid_form)['valid'])
        #invalid date
        test_form = invalid_form.copy()
        test_form['g587-birthday'] = "01/01/1890"
        self.assertFalse(validation.validate_form(test_form)['valid'])
        # invalid_postal_code
        test_form = invalid_form.copy()
        test_form["g587-zipcode"] = "00000"
        self.assertFalse(validation.validate_form(test_form)['valid'])
        # invalid_email
        test_form = invalid_form.copy()
        test_form["g587-email"] = "maadsf"
        self.assertFalse(validation.validate_form(test_form)['valid'])

    def tearDown(self):
        pass


class TestPostalCheck(unittest.TestCase):

    def setUp(self):
        pass

    def test_postal_code(self):
        self.assertTrue(validation.postal_code("22308")['valid'])


class TestBoundaryCheck(unittest.TestCase):

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
            "street": "400 smith level rd #e-21",
            # "street": "500 smith level rd",
            "state": "NC",
            "postal_code": "27510",
        }
        self.bad_address = {
            "city": "asdf",
            "state": "qw",
            "postal_code": "00000",
            "street": "1adfadffdsf"
        }

    def test_boundary_within(self):
        self.assertTrue(validation.boundary_check(**self.valid_address)['valid'])

    def test_bounday_not_within(self):
        self.assertFalse(validation.boundary_check(**self.out_boundary_address)['valid'])

    def test_unable_to_determine(self):
        self.assertIsNone(validation.boundary_check(**self.bad_address)['valid'])


if __name__ == '__main__':
    unittest.main()
