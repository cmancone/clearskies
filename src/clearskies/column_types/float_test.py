import unittest
from .float import Float


class FloatTest(unittest.TestCase):
    def test_from_backend(self):
        float_column = Float("di")
        self.assertEquals(5.0, float_column.from_backend("5"))

    def test_to_backend(self):
        float_column = Float("di")
        float_column.name = "age"

        self.assertEquals({"name": "hey", "age": 5.0}, float_column.to_backend({"name": "hey", "age": "5"}))
        # These two are just to make sure it doesn't crash if there is no data
        # which is allowed and normal
        self.assertEquals({"name": "hey"}, float_column.to_backend({"name": "hey"}))
        self.assertEquals({"name": "hey", "age": None}, float_column.to_backend({"name": "hey", "age": None}))

    def test_check_input_bad(self):
        float_column = Float("di")
        float_column.configure("age", {}, FloatTest)
        error = float_column.input_errors("model", {"age": "asdf"})
        self.assertEquals({"age": "Invalid input: age must be an integer or float"}, error)

    def test_check_input_good(self):
        float_column = Float("di")
        float_column.configure("age", {}, FloatTest)
        self.assertEquals({}, float_column.input_errors("model", {"age": 15.05}))
        self.assertEquals({}, float_column.input_errors("model", {"age": 15}))
        self.assertEquals({}, float_column.input_errors("model", {"age": None}))
        self.assertEquals({}, float_column.input_errors("model", {}))

    def test_is_allowed_operator(self):
        float_column = Float("di")
        for operator in ["=", "<", ">", "<=", ">="]:
            self.assertTrue(float_column.is_allowed_operator(operator))
        for operator in ["==", "<=>"]:
            self.assertFalse(float_column.is_allowed_operator(operator))

    def test_build_condition(self):
        float_column = Float("di")
        float_column.configure("fraction", {}, int)
        self.assertEquals("fraction=0.2", float_column.build_condition(0.2))
        self.assertEquals("fraction<10", float_column.build_condition(10, operator="<"))

    def test_check_search_value(self):
        float_column = Float("di")
        self.assertEquals("", float_column.check_search_value(25))
        self.assertEquals("", float_column.check_search_value(25.0))
        self.assertEquals("value should be an integer or float", float_column.check_search_value("asdf"))
