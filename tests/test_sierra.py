import unittest
import chplpatron.sierra as sierra

from chplpatron.exceptions import *


class TestGetToken(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_token(self):
        token = sierra.get_token()
        self.assertIsNotNone(token)

    def tearDown(self):
        pass


class TestRegister(unittest.TestCase):

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


class TestSetEmail(unittest.TestCase):

    def setUp(self):
        pass

    def test_lookup_name(self):
        result = sierra.lookup_by_name("Ztestd, Jess")
        # patron = sierra.Patron()
        # patron.pin = "121212"
        # sierra.update_patron(patron, result.get("id"))
        pprint.pprint(result)

    def tearDown(self):
        pass


class TestSetMessages(unittest.TestCase):

    def setUp(self):
        pass

    def test_lookup_name(self):
        msg = sierra.VarField()
        msg.fieldTag = "m"
        msg.content = "Not in boundary message"

        note = sierra.VarField()
        note.fieldTag = "x"
        note.content = "Not in boundary note"

        # Ztestd, Jess - id: 354311
        # set NO pMessage and VarField('m', "Not in boundary message")
        id = 354311
        patron = sierra.Patron()
        patron.patronType = 16
        # patron.varFields = [msg, note]
        sierra.update_patron(patron, id)
        result = sierra.lookup_by_id(id)
        print(result.get('names')[0], " - id: ", id)
        print("pMessage :", result.get('pMessage'))
        print("patronType: ", result.get("patronType"))
        pprint.pprint(result.get('varFields'))

        # Zteste, Jack - id: 354313
        # set pMessage = 'f' - no varfield message
        id = 354313
        patron = sierra.Patron()
        # patron.pMessage = 'f'
        # patron.varFields = note
        patron.patronType = 16
        sierra.update_patron(patron, id)
        result = sierra.lookup_by_id(id)
        print(result.get('names')[0], " - id: ", id)
        print("pMessage :", result.get('pMessage'))
        print("patronType: ", result.get("patronType"))
        pprint.pprint(result.get('varFields'))

        # Ztestb, Jane - id: 354240
        # set pMessage: 'f' and VarField('m', "Not in boundary message")
        id = 354240
        patron = sierra.Patron()
        # patron.pMessage = 'f'
        # patron.varFields = [msg, note]
        patron.patronType = 16
        sierra.update_patron(patron, id)
        result = sierra.lookup_by_id(id)
        print(result.get('names')[0], " - id: ", id)
        print("pMessage :", result.get('pMessage'))
        print("patronType: ", result.get("patronType"))
        pprint.pprint(result.get('varFields'))

    def tearDown(self):
        pass


class TestFindById(unittest.TestCase):

    def setUp(self):
        pass

    def test_lookup_id(self):
        result = sierra.lookup_by_id(354316)

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
