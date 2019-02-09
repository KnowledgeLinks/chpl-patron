import unittest
import requests
from chplpatron.registration.utilities import Flds


class TestLiveApi(unittest.TestCase):
    base_url = "https://chapelhillpubliclibrary.org/register/"
    valid_address = {'g587-address': '100 Library Drive',
                     'g587-city': 'Chapel Hill',
                     'g587-state': 'NC',
                     'g587-zipcode': '27514'}

    out_boundary_address = {'g587-address': '101 Independence Ave SE',
                            'g587-city': 'Washington',
                            'g587-state': 'DC',
                            'g587-zipcode': '20540'}

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
        result = requests.get(url[:-1])
        self.assertEqual(result.status_code, 405)

    def test_check_boundary(self):
        url = self.base_url + "boundary_check"
        result = requests.get(url, params=self.out_boundary_address)
        self.assertFalse(result.json().get("valid"))
        result = requests.get(url, params=self.valid_address)
        self.assertTrue(result.json().get("valid"))

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
