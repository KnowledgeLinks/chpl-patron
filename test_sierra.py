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

class Test_register(unittest.TestCase):

    def setUp(self):
        pass

    def test_register_empty_payload(self):
        result = sierra.register({})
        self.assertEqual(result.status_code,
                         400)
        self.assertEqual(result.json().get('code'),
                         130)
        self.assertEqual(result.json().get('name'),
            'Bad JSON/XML Syntax')

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
