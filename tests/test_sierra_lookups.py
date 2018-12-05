import unittest
import pprint
import simplejson

from chplpatron.sierra import lookups


class Test_get_url(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_token(self):
        urls = lookups.Urls()
        print(urls.modes)
        print(urls.patron([0, 1]))
        print(urls.find(["n", "Deed" ]))
        print(urls.token())

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
