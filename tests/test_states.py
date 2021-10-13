import unittest
from chplpatron.postaldb import states

from chplpatron.exceptions import InvalidState


class TestStates(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_name(self):
        self.assertEqual(states.get_name("va"), "Virginia")
        self.assertEqual(states.get_name("VA"), "Virginia")
        self.assertEqual(states.get_name("Virginia"), "Virginia")
        self.assertEqual(states.get_name("virginia"), "Virginia")
        self.assertRaises(InvalidState,
                          states.get_name, "adfadf")

    def test_get_abbreviation(self):
        self.assertEqual(states.get_abbreviation("va"), "VA")
        self.assertEqual(states.get_abbreviation("virginia"), "VA")
        self.assertEqual(states.get_abbreviation("VA"), "VA")
        self.assertEqual(states.get_abbreviation("VIRGINIA"), "VA")
        self.assertRaises(InvalidState,
                          states.get_name, "ZZ")

    def test_is_state(self):
        self.assertTrue(states.is_state("VA"))
        self.assertFalse(states.is_state("asdfasdf"))

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
