import unittest
import requests
from chplpatron.registration.utilities import Flds


class TestLiveApi(unittest.TestCase):
    base_url = "https://chapelhillpubliclibrary.org/register/"

    def setUp(self):
        pass

    def test_postal_code(self):
        url = self.base_url + "postal_code"
        result = requests.get(url + "?" + Flds.postal_code.frm + "=22308").json()
        self.assertTrue(result.get("valid"))

    def test_email_check(self):
        url = self.base_url + "email_check"
        result = requests.get(url + "?" + Flds.email.frm + "=notreg@email.com").json()
        self.assertTrue(result)

    def test_statistics_reg_by_month(self):
        url = self.base_url + "statistics/reg_by_month"
        result = requests.get(url).json()
        self.assertGreater(len(result), 0)

    def test_fail_register_with_get(self):
        url = self.base_url
        result = requests.get(url)
        self.assertEqual(result.status_code, 405)

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
