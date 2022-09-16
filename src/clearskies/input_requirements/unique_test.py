import unittest
from unittest.mock import MagicMock
from .unique import Unique
class UniqueTest(unittest.TestCase):
    def setUp(self):
        self.exists = type('', (), {'exists': True, '__getattr__': MagicMock(return_value='sup')})()
        self.does_not_exist = type('', (), {'exists': False})()
        self.find_exists = MagicMock(return_value=type('', (), {'exists': True})())
        self.find_does_not_exist = MagicMock(return_value=type('', (), {'exists': False})())
        self.unique = Unique()
        self.unique.configure()
        self.unique.column_name = 'name'

    def test_misc(self):
        # if we're not setting and it doesn't exist then no problems
        error = self.unique.check(self.does_not_exist, {})
        self.assertEquals('', error)
        # if we're setting to the same value then we're good
        error = self.unique.check(self.exists, {'name': 'sup'})
        self.assertEquals('', error)
        # if we're setting to a new value that doesn't exist then we're good
        self.exists.find = self.find_does_not_exist
        error = self.unique.check(self.exists, {'name': 'cool'})
        self.assertEquals('', error)
        self.find_does_not_exist.assert_called_with('name=cool')
        # if we're setting to a new value and that does exist then we have trouble
        self.exists.find = self.find_exists
        error = self.unique.check(self.exists, {'name': 'cool'})
        self.assertEquals("Invalid value for 'name': the given value already exists, and must be unique.", error)
        self.find_exists.assert_called_with('name=cool')
        # ditto if it doesn't exist
        self.does_not_exist.find = self.find_exists
        error = self.unique.check(self.does_not_exist, {'name': 'cool'})
        self.assertEquals("Invalid value for 'name': the given value already exists, and must be unique.", error)
        self.find_does_not_exist.assert_called_with('name=cool')
