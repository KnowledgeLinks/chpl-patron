import unittest
import requests
import string
import random
import pprint
import json
from chplpatron.registration.utilities import Flds


def random_email():
    choices = string.ascii_lowercase + string.digits
    return "{}@{}.{}".format(random.choice(choices),
                             random.choice(choices),
                             random.choice(choices))


class TestLiveApi(unittest.TestCase):
    base_url = "https://chapelhillpubliclibrary.org/register/"
    # base_url = "http://localhost:8443/register/"
    valid_address = {'g5'
                     '87-address': '100 Library Drive',
                     'g587-city': 'Chapel Hill',
                     'g587-state': 'NC',
                     Flds.postal_code.frm: '27514'}

    out_boundary_address = {'g587-address': '101 Independence Ave SE',
                            'g587-city': 'Washington',
                            'g587-state': 'DC',
                            'g587-zipcode': '20540'}
    valid_form_base = {Flds.first_name.frm: "Mike",
                       Flds.birthday.frm: "1/1/1950",
                       Flds.last_name.frm: "Ztesta",
                       Flds.email.frm: random_email(),
                       Flds.password.frm: "1234qwer",
                       "testing": True}

    valid_out_boundary_form = valid_form_base.copy().update(out_boundary_address)

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

    def test_valid_form_in_boundary(self):
        valid_in_boundary_form = self.valid_form_base.copy()
        valid_in_boundary_form.update(self.valid_address)
        session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0'}
        result = session.post(self.base_url[:-1], headers=headers, data=valid_in_boundary_form)
        self.assertTrue("boundary=true" in result.json().get("url", ""))

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
