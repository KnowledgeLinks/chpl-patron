import unittest
import pprint
from chplpatron.sierra.patron import *
from chplpatron import sierra


class TestPatron(unittest.TestCase):

    def test_patron_init(self):
        patron = Patron()
        for attr, val in patron.attributes().items():
            self.assertTrue(val is None
                            or (isinstance(val, list) and len(val) == 0),
                            attr)

    # def test_set_attr(self):
    #     # data = sierra.lookup_by_name("Ztestb, Jane")
    #     # pprint.pprint(data)
    #     # patron = Patron(data)
    #     patron = Patron()
    #     # patron.names = "Stabile, Michael"
    #     patron.emails = "mstabile75@gmail.com"
    #     # patron.varFields = {'fieldTag': "z"}
    #     p = patron.to_dict()
    #     pprint.pprint(p)


    def test_create_patron(self):
        # id = sierra.lookup_by_name("Ztesta, Joe").get('id')
        sierra.delete_patron(id)
        patron = Patron()
        patron.emails = "j@j.com"
        patron.names = "Ztesta, Jane"
        address = Address()
        address.type = "h"
        address.lines = ["9913 Shady Cove Dr",
                         "Fairfax Station, VA 22039"]
        patron.addresses = address
        patron.patronType = 15
        patron.birthDate = "2001-01-01"
        patron.expirationDate = "2019-01-26"
        phone = Phone()
        phone.number = "760-809-3661"
        phone.type = 't'
        patron.phones = phone
        patron.pin = "1234qwer"
        var_field = sierra.VarField()
        var_field.fieldTag = "x"
        var_field.content = "test message"
        patron.varFields = var_field
        p = patron.to_dict()
        pprint.pprint(p)
        result = sierra.create_patron(patron)
        pprint.pprint(result)


if __name__ == '__main__':
    unittest.main()
