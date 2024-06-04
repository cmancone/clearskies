import unittest
from unittest.mock import MagicMock
from .minimum_value import MinimumValue


class MinimumValueTest(unittest.TestCase):
    def setUp(self):
        self.minimum_value = MinimumValue()
        self.minimum_value.column_name = "age"

    def test_check_length(self):
        self.minimum_value.configure(1)

        error = self.minimum_value.check("model", {"age": "10"})
        self.assertEqual("", error)
        error = self.minimum_value.check("model", {"age": 10})
        self.assertEqual("", error)
        error = self.minimum_value.check("model", {"age": ""})
        self.assertEqual("", error)
        error = self.minimum_value.check("model", {})
        self.assertEqual("", error)
        error = self.minimum_value.check("model", {"age": -1})
        self.assertEqual("'age' must be at least 1.", error)

    def test_check_configuration_value_not_int(self):
        with self.assertRaises(ValueError) as context:
            self.minimum_value.configure("10")
        self.assertEqual(
            "Minimum value must be an int to use the MinimumValue class for column 'age'", str(context.exception)
        )
