import unittest
from unittest.mock import MagicMock
from .maximum_value import MaximumValue


class MaximumValueTest(unittest.TestCase):
    def setUp(self):
        self.maximum_value = MaximumValue()
        self.maximum_value.column_name = "age"

    def test_check_length(self):
        self.maximum_value.configure(10)

        error = self.maximum_value.check("model", {"age": "10"})
        self.assertEqual("", error)
        error = self.maximum_value.check("model", {"age": 10})
        self.assertEqual("", error)
        error = self.maximum_value.check("model", {"age": ""})
        self.assertEqual("", error)
        error = self.maximum_value.check("model", {})
        self.assertEqual("", error)
        error = self.maximum_value.check("model", {"age": -5})
        self.assertEqual("", error)
        error = self.maximum_value.check("model", {"age": 11})
        self.assertEqual("'age' must be at most 10.", error)

    def test_check_configuration_value_not_int(self):
        with self.assertRaises(ValueError) as context:
            self.maximum_value.configure("10")
        self.assertEqual(
            "Maximum value must be an int to use the MaximumValue class for column 'age'", str(context.exception)
        )
