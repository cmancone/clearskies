import unittest
from .boolean import Boolean


class BooleanTest(unittest.TestCase):
    def test_from_backend(self):
        boolean = Boolean("di")
        self.assertEqual(True, boolean.from_backend("1"))

    def test_to_backend(self):
        boolean = Boolean("di")
        boolean.name = "old"

        self.assertEqual({"name": "hey", "old": True}, boolean.to_backend({"name": "hey", "old": "1"}))
        # These two are just to make sure it doesn't crash if there is no data
        # which is allowed and normal
        self.assertEqual({"name": "hey"}, boolean.to_backend({"name": "hey"}))
        self.assertEqual({"name": "hey", "age": None}, boolean.to_backend({"name": "hey", "age": None}))

    def test_check_input_bad(self):
        boolean = Boolean("di")
        boolean.configure("age", {}, BooleanTest)
        error = boolean.input_errors("model", {"age": "asdf"})
        self.assertEqual({"age": "age must be a boolean"}, error)

    def test_check_input_good(self):
        boolean = Boolean("di")
        boolean.configure("age", {}, BooleanTest)
        self.assertEqual({}, boolean.input_errors("model", {"age": True}))
        self.assertEqual({}, boolean.input_errors("model", {"age": None}))
        self.assertEqual({}, boolean.input_errors("model", {}))

    def test_is_allowed_operator(self):
        boolean = Boolean("di")
        for operator in ["="]:
            self.assertTrue(boolean.is_allowed_operator(operator))
        for operator in ["<", ">", "<=", ">="]:
            self.assertFalse(boolean.is_allowed_operator(operator))
        for operator in ["==", "<=>"]:
            self.assertFalse(boolean.is_allowed_operator(operator))

    def test_build_condition(self):
        boolean = Boolean("di")
        boolean.configure("fraction", {}, int)
        self.assertEqual("fraction=1", boolean.build_condition(True))
        self.assertEqual("fraction=0", boolean.build_condition(""))

    def test_check_search_value(self):
        boolean = Boolean("di")
        boolean.configure("age", {}, BooleanTest)
        self.assertEqual("", boolean.check_search_value(True))
        self.assertEqual("age must be a boolean", boolean.check_search_value(25.0))
        self.assertEqual("age must be a boolean", boolean.check_search_value("asdf"))
