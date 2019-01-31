import unittest
import os

from chplpatron import trackingdb
from chplpatron.exceptions import RegisteredEmailError


class Test_TrackingDb(unittest.TestCase):
    test_email = "testemail@gmail.com"

    def setUp(self):
        # creates a test database and adds one record to it.
        trackingdb.trackingdb.DB_NAME = "test_tracking_db.sqlite"
        trackingdb.trackingdb.TRACKING_DB_SETUP = False
        trackingdb.trackingdb.setup(None)
        try:
            trackingdb.add_registration(10, self.test_email)
        except RegisteredEmailError:
            pass

    def test_add_registration(self):
        self.assertRaises(RegisteredEmailError,
                          trackingdb.add_registration,
                          10,
                          self.test_email)

    def test_lookup_email(self):
        self.assertIsNotNone(trackingdb.lookup_email(self.test_email))
        self.assertIsNone(trackingdb.lookup_email("none@email.com"))
        self.assertEqual(trackingdb.lookup_email(self.test_email)[4],
                         trackingdb.hash_email(self.test_email))
        self.assertTrue("@" not in trackingdb.lookup_email(self.test_email))

    def test_lookup_card_number(self):
        self.assertIsNotNone(trackingdb.lookup_card_number(10))
        self.assertIsNone(trackingdb.lookup_card_number(12))

    # def test_load_old_data(self):
    #     trackingdb.trackingdb.load_old_data("/home/stabiledev/git/"
    #                                         "chpl-patron/card-requests.sqlite")

    def tearDown(self):
        # deletes the test database
        os.remove(trackingdb.trackingdb.DB_PATH)


if __name__ == '__main__':
    unittest.main()
