import unittest
import chplpatron.sierra as sierra

from chplpatron.chplexceptions import *


class Test_get_token(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_token(self):
        token = sierra.get_token()
        self.assertIsNotNone(token)

    def tearDown(self):
        pass


class Test_register(unittest.TestCase):

    def setUp(self):
        pass

    def test_register_empty_payload(self):
        result = sierra.register({})
        self.assertEqual(result.status_code,
                         400)
        self.assertEqual(result.json().get('code'),
                         130)
        self.assertEqual(result.json().get('name'),
                         'Bad JSON/XML Syntax')

    def tearDown(self):
        pass


class Test_email_check(unittest.TestCase):

    def setUp(self):
        pass

    def test_email(self):
        self.assertRaises(RegisteredEmailError,
                          sierra.email_check,
                          "stabilemichael@hotmail.com")
        self.assertTrue(sierra.email_check("not_reg_email@gmail.com"))
        # temp card number 353980
        
    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
