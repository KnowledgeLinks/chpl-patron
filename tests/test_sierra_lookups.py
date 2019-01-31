import unittest
import pprint
import simplejson

from chplpatron.sierra import lookups


class Test_Urls(unittest.TestCase):

    def setUp(self):
        pass

    def test_urls(self):
        urls = lookups.Urls()
        rtn_url = ('https://catalog.chapelhillpubliclibrary.org/iii/'
                   'sierra-api/v5/patrons/find?varFieldTag=n&'
                   'varFieldContent=DOE%2C+JOHN')
        self.assertEqual(urls.find(["n", "DOE, JOHN"]), rtn_url)
        self.assertEqual(urls.find({"varFieldTag": "n",
                                    "varFieldContent": "DOE, JOHN"}), rtn_url)
        self.assertEqual(urls.find("varFieldTag=n&"
                                   "varFieldContent=DOE%2C+JOHN"), rtn_url)
        self.assertRaises(lookups.UrlMissingKeyId, urls.patron_update)
        url = ("https://catalog.chapelhillpubliclibrary.org/iii/"
               "sierra-api/v5/patrons/1234")
        self.assertEqual(urls.patron_update("1234"), url)
        self.assertEqual(urls.patron_update(1234), url)
        self.assertEqual(urls.patron_update(["1234"]), url)
        self.assertEqual(urls.patron_update({"key":"1234"}), url)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
