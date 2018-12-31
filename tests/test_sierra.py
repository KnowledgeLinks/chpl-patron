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

        result = sierra.create_patron(sierra.Patron())
        self.assertEqual(result, "")

    def tearDown(self):
        pass


class TestCheckEmail(unittest.TestCase):

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


class TestFindByName(unittest.TestCase):

    def setUp(self):
        pass

    def test_lookup_name(self):
        result = sierra.lookup_by_name("Ztestd, Jess")
        # sierra.set_email("m@m.com", result['id'])
        pprint.pprint(result)

    def tearDown(self):
        pass


class TestFindById(unittest.TestCase):

    def setUp(self):
        pass

    def test_lookup_id(self):
        result = sierra.lookup_by_id(352695)

        pprint.pprint(result)

    def tearDown(self):
        pass


class TestSetters(unittest.TestCase):

    def setUp(self):
        pass

    def test_put_data(self):
        # patron = sierra.Patron()
        # patron.names = "Ztestc, Joan"
        # patron.emails = "mstabile75@gmail.com"
        # result = sierra.update_patron(patron, 354241)
        # print(result)
        # pprint.pprint(sierra.lookup_by_id(354241))
        # sierra.set_barcode(354240, 354240)
        pass


if __name__ == '__main__':
    unittest.main()
