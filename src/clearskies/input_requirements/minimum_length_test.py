import unittest
from unittest.mock import MagicMock
from .minimum_length import MinimumLength


class MinimumLengthTest(unittest.TestCase):
    def setUp(self):
        self.minimum_length = MinimumLength()
        self.minimum_length.column_name = 'name'

    def test_check_length(self):
        self.minimum_length.configure(10)

        error = self.minimum_length.check('model', {'name': '1234567890'})
        self.assertEquals('', error)
        error = self.minimum_length.check('model', {'name': ''})
        self.assertEquals('', error)
        error = self.minimum_length.check('model', {})
        self.assertEquals('', error)
        error = self.minimum_length.check('model', {'name': '12345678901'})
        self.assertEquals('', error)
        error = self.minimum_length.check('model', {'name': '123456789'})
        self.assertEquals("'name' must be at least 10 characters long.", error)

    def test_check_configuration_length_not_int(self):
        with self.assertRaises(ValueError) as context:
            self.minimum_length.configure('asdf')
        self.assertEquals(
            "Minimum length must be an int to use the MinimumLength class for column 'name'",
            str(context.exception)
        )
