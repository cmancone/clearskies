import unittest
from .string import String


class StringTest(unittest.TestCase):
    def test_is_allowed_operator(self):
        string = String()
        for operator in ['=', 'LIKE']:
            self.assertTrue(string.is_allowed_operator(operator))
        for operator in ['==', '<=>']:
            self.assertFalse(string.is_allowed_operator(operator))

    def test_build_condition(self):
        string = String()
        string.configure('name', {}, int)
        self.assertEquals('name=sup', string.build_condition('sup', operator='='))
        self.assertEquals("name LIKE '%asdf%'", string.build_condition('asdf', operator='like'))
        self.assertEquals("name LIKE '%asdf%'", string.build_condition('asdf'))

    def test_check_search_value(self):
        string = String()
        self.assertEquals('', string.check_search_value('sup'))
        self.assertEquals('value should be a string', string.check_search_value(10))
