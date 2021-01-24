import unittest
from unittest.mock import MagicMock
from .required import Required


class RequiredTest(unittest.TestCase):
    def setUp(self):
        self.does_exist = type('', (), {
            'exists': True,
            '__getitem__': MagicMock(return_value='sup')
        })()
        self.does_not_exist = type('', (), {'exists': False})()
        self.required = Required()
        self.required.configure()
        self.required.column_name = 'name'

    def test_create(self):
        error = self.required.check(self.does_not_exist, {})
        self.assertEquals("'name' is required.", error)
        error = self.required.check(self.does_not_exist, {'name': ' '})
        self.assertEquals("'name' is required.", error)
        error = self.required.check(self.does_not_exist, {'name': 0})
        self.assertEquals("'name' is required.", error)

        error = self.required.check(self.does_not_exist, {'name': 'sup'})
        self.assertEquals('', error)
        error = self.required.check(self.does_not_exist, {'name': 5})
        self.assertEquals('', error)

    def test_update(self):
        # The database already has a value for the required field
        self.does_exist.__getitem__ = MagicMock(return_value='okay')
        error = self.required.check(self.does_exist, {'name': '  '})
        self.assertEquals("'name' is required.", error)
        error = self.required.check(self.does_exist, {'name': 'hey'})
        self.assertEquals('', error)
        error = self.required.check(self.does_exist, {})
        self.assertEquals('', error)

        # The database does not have a value for the required field
        exists_no_value = type('', (), {
            'exists': True,
            '__getitem__': MagicMock(return_value='')
        })()
        error = self.required.check(self.does_exist, {'name': '   '})
        self.assertEquals("'name' is required.", error)
        error = self.required.check(exists_no_value, {})
        self.assertEquals("'name' is required.", error)
        error = self.required.check(self.does_exist, {'name': 'okay'})
        self.assertEquals("", error)
