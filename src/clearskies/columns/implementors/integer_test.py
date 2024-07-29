import unittest
from .integer import Integer


class IntegerTest(unittest.TestCase):
    def test_from_backend(self):
        integer = Integer("di")
        self.assertEqual(5, integer.from_backend("5"))

    def test_to_backend(self):
        integer = Integer("di")
        integer.name = "age"

        self.assertEqual({"name": "hey", "age": 5}, integer.to_backend({"name": "hey", "age": "5"}))
        # These two are just to make sure it doesn't crash if there is no data
        # which is allowed and normal
        self.assertEqual({"name": "hey"}, integer.to_backend({"name": "hey"}))
        self.assertEqual({"name": "hey", "age": None}, integer.to_backend({"name": "hey", "age": None}))

    def test_check_input_bad(self):
        integer = Integer("di")
        integer.configure("age", {}, IntegerTest)
        error = integer.input_errors("model", {"age": "asdf"})
        self.assertEqual({"age": "age must be an integer"}, error)

    def test_check_input_good(self):
        integer = Integer("di")
        integer.configure("age", {}, IntegerTest)
        self.assertEqual({}, integer.input_errors("model", {"age": 15}))
        self.assertEqual({}, integer.input_errors("model", {"age": None}))
        self.assertEqual({}, integer.input_errors("model", {}))

    def test_is_allowed_operator(self):
        integer = Integer("di")
        for operator in ["=", "<", ">", "<=", ">="]:
            self.assertTrue(integer.is_allowed_operator(operator))
        for operator in ["==", "<=>"]:
            self.assertFalse(integer.is_allowed_operator(operator))

    def test_build_condition(self):
        integer = Integer("di")
        integer.configure("fraction", {}, int)
        self.assertEqual("fraction=0.2", integer.build_condition(0.2))
        self.assertEqual("fraction<10", integer.build_condition(10, operator="<"))

    def test_check_search_value(self):
        integer = Integer("di")
        integer.configure("age", {}, IntegerTest)
        self.assertEqual("", integer.check_search_value(25))
        self.assertEqual("age must be an integer", integer.check_search_value(25.0))
        self.assertEqual("age must be an integer", integer.check_search_value("asdf"))
