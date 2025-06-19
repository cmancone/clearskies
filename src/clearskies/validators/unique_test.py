import unittest
from unittest.mock import MagicMock

import clearskies

from .unique import Unique


class MyModel(clearskies.Model):
    id_column_name = "id"
    backend = clearskies.backends.MemoryBackend()
    id = clearskies.columns.Uuid()
    name = clearskies.columns.String()


class UniqueTest(unittest.TestCase):
    def setUp(self):
        di = clearskies.di.Di()
        self.my_models = di.build(MyModel)
        self.bob = self.my_models.create({"name": "Bob"})
        self.jane = self.my_models.create({"name": "Jane"})

        self.unique = Unique()

    def test_misc(self):
        # if we're not setting and it doesn't exist then no problems
        error = self.unique.check(self.my_models.model(), "name", {})
        self.assertEqual("", error)
        # if we're setting to the same value then we're good
        error = self.unique.check(self.bob, "name", {"name": "sup"})
        self.assertEqual("", error)
        # if we're setting to a new value that doesn't exist then we're good
        error = self.unique.check(self.bob, "name", {"name": "cool"})
        self.assertEqual("", error)
        # if we're setting to a new value and that does exist then we have trouble
        error = self.unique.check(self.bob, "name", {"name": "Jane"})
        self.assertEqual("Invalid value for 'name': the given value already exists, and must be unique.", error)
        # ditto if it doesn't exist
        error = self.unique.check(self.my_models.model(), "name", {"name": "Jane"})
        self.assertEqual("Invalid value for 'name': the given value already exists, and must be unique.", error)
