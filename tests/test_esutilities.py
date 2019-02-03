import unittest

import datetime

from chplpatron.statistics import esutilities


class TestAgeRangeConversion(unittest.TestCase):

    def setUp(self):
        pass

    def test_conv_birthdate_to_age(self):
        birthday = datetime.date(2000, 1, 1)
        age = esutilities.conv_birthdate_to_age(birthday)
        self.assertTrue(age>18)

    def test_conv_to_age_range(self):
        for rng in esutilities.AGE_RANGES:
            self.assertEqual(esutilities.conv_to_age_range(rng[0]), rng[1])
            self.assertEqual(esutilities.conv_to_age_range(rng[0]-2), rng[1])
            self.assertNotEqual(esutilities.conv_to_age_range(rng[0]+1), rng[1])

    def tearDown(self):
        pass
