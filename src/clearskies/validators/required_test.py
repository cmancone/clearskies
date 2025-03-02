import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from .required import Required


class RequiredTest(unittest.TestCase):
    def setUp(self):
        self.required = Required()

    def test_create(self):
        error = self.required.check(False, "name", {})
        self.assertEqual("'name' is required.", error)
        error = self.required.check(False, "name", {"name": " "})
        self.assertEqual("'name' is required.", error)
        error = self.required.check(False, "name", {"name": 0})
        self.assertEqual("'name' is required.", error)

        error = self.required.check(False, "name", {"name": "sup"})
        self.assertEqual("", error)
        error = self.required.check(False, "name", {"name": 5})
        self.assertEqual("", error)

    def test_update(self):
        # The database already has a value for the required field
        exists = SimpleNamespace(name="sup")
        error = self.required.check(exists, "name", {"name": "  "})
        self.assertEqual("'name' is required.", error)
        error = self.required.check(exists, "name", {"name": "hey"})
        self.assertEqual("", error)
        error = self.required.check(exists, "name", {})
        self.assertEqual("", error)

        # The database does not have a value for the required field
        exists_no_value = SimpleNamespace(name="")
        error = self.required.check(exists_no_value, "name", {"name": "   "})
        self.assertEqual("'name' is required.", error)
        error = self.required.check(exists_no_value, "name", {})
        self.assertEqual("'name' is required.", error)
        error = self.required.check(exists_no_value, "name", {"name": "okay"})
        self.assertEqual("", error)
