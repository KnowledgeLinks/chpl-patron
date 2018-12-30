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

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
