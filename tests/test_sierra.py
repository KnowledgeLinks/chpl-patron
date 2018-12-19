import unittest
import chplpatron.sierra as sierra

from chplpatron.exceptions import *


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
        result = sierra.create_patron({})
        self.assertEqual(result.status_code,
                         400)
        self.assertEqual(result.json().get('code'),
                         130)
        self.assertEqual(result.json().get('name'),
                         'Bad JSON/XML Syntax')

    def tearDown(self):
        pass


class Test_check_email(unittest.TestCase):

    def setUp(self):
        pass

    def test_email(self):
        self.assertRaises(RegisteredEmailError,
                          sierra.check_email,
                          "stabilemichael@hotmail.com")
        self.assertTrue(sierra.check_email("not_reg_email@gmail.com"))
        # temp card number 353980
        pprint.pprint(sierra.lookup_by_email("stabilemichael@hotmail.com"))

    def tearDown(self):
        pass


class Test_find_by_name(unittest.TestCase):

    def setUp(self):
        pass

    def test_lookup_name(self):
        pprint.pprint(sierra.lookup_by_name("Ztestb, Jane"))

    def tearDown(self):
        pass


class Test_setters(unittest.TestCase):

    def setUp(self):
        pass

    def test_put_data(self):
        print(sierra.set_email(354053, "stabilemichael@hotmail.com"))
        pass


if __name__ == '__main__':
    unittest.main()
