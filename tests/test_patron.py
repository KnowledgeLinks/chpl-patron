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

    def test_set_attr(self):
        data = sierra.lookup_by_name("Ztestb, Jane")
        # pprint.pprint(data)
        patron = Patron(data)
        patron.names = "Stabile, Michael"
        patron.emails = "mstabile75@gmail.com"
        patron.varFields = {'fieldTag': "z"}
        p = patron.to_dict()
        pprint.pprint(p)


if __name__ == '__main__':
    unittest.main()
