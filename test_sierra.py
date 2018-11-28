import unittest
import sierra 

class Test_get_token(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_token(self):
        token = sierra.get_token()
        self.assertIsNotNone(token)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
