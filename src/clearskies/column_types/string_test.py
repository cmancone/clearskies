import unittest
from .string import String


class StringTest(unittest.TestCase):
    def test_is_allowed_operator(self):
        string = String("di")
        for operator in ["=", "LIKE"]:
            self.assertTrue(string.is_allowed_operator(operator))
        for operator in ["==", "<=>"]:
            self.assertFalse(string.is_allowed_operator(operator))

    def test_build_condition(self):
        string = String("di")
        string.configure("name", {}, int)
        self.assertEqual("name=sup", string.build_condition("sup", operator="="))
        self.assertEqual("name LIKE '%asdf%'", string.build_condition("asdf", operator="like"))
        self.assertEqual("name=asdf", string.build_condition("asdf"))

    def test_check_search_value(self):
        string = String("di")
        self.assertEqual("", string.check_search_value("sup"))
        self.assertEqual("value should be a string", string.check_search_value(10))
