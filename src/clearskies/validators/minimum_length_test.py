import unittest
from unittest.mock import MagicMock

from .minimum_length import MinimumLength


class MinimumLengthTest(unittest.TestCase):
    def setUp(self):
        self.minimum_length = MinimumLength(10)

    def test_check_length(self):
        error = self.minimum_length.check("model", "name", {"name": "12345678901"})
        self.assertEqual("", error)
        error = self.minimum_length.check("model", "name", {"name": ""})
        self.assertEqual("", error)
        error = self.minimum_length.check("model", "name", {})
        self.assertEqual("", error)
        error = self.minimum_length.check("model", "name", {"name": "123456789"})
        self.assertEqual("'name' must be at least 10 characters long.", error)
