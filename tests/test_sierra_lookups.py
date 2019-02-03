import unittest
import pprint
import simplejson

from chplpatron.sierra import lookups


class TestUrls(unittest.TestCase):

    def setUp(self):
        pass

    def test_urls(self):
        urls = lookups.Apis()
        rtn_url = ('https://catalog.chapelhillpubliclibrary.org/iii/'
                   'sierra-api/v5/patrons/find?varFieldTag=n&'
                   'varFieldContent=DOE%2C+JOHN')
        self.assertEqual(urls.find(["n", "DOE, JOHN"], test=True), rtn_url)
        self.assertEqual(urls.find({"varFieldTag": "n",
                                    "varFieldContent": "DOE, JOHN"}, test=True), rtn_url)
        self.assertEqual(urls.find("varFieldTag=n&"
                                   "varFieldContent=DOE%2C+JOHN", test=True), rtn_url)
        self.assertRaises(lookups.UrlMissingKeyId, urls.patron_update)
        url = ("https://catalog.chapelhillpubliclibrary.org/iii/"
               "sierra-api/v5/patrons/1234")
        self.assertEqual(urls.patron_update("1234", test=True), url)
        self.assertEqual(urls.patron_update(1234, test=True), url)
        self.assertEqual(urls.patron_update(["1234"], test=True), url)
        self.assertEqual(urls.patron_update({"key": "1234"}, test=True), url)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
